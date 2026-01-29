#include "mythreads.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>

static TCB* current_thread = NULL;
static TCB* ready_queue[3] = {NULL, NULL, NULL};  // One queue per priority level
static TCB* all_threads = NULL;
static int next_tid = 1;
static struct itimerval timer;
static ucontext_t scheduler_context;
static bool scheduler_initialized = false;

// Function to add thread to ready queue based on priority
static void enqueue_thread(TCB* thread) {
    if (!thread) return;
    
    thread->state = READY;
    int prio = thread->priority;
    
    if (!ready_queue[prio]) {
        ready_queue[prio] = thread;
        thread->next = NULL;
    } else {
        TCB* curr = ready_queue[prio];
        while (curr->next) {
            curr = curr->next;
        }
        curr->next = thread;
        thread->next = NULL;
    }
}

// Function to get highest priority thread from ready queues
static TCB* dequeue_highest_priority_thread(void) {
    // Check from HIGH to LOW priority
    for (int prio = HIGH; prio >= LOW; prio--) {
        if (ready_queue[prio]) {
            TCB* thread = ready_queue[prio];
            ready_queue[prio] = thread->next;
            thread->next = NULL;
            return thread;
        }
    }
    return NULL;
}

// Timer interrupt handler (for preemption)
static void timer_handler(int sig) {
    if (current_thread && current_thread->state == RUNNING) {
        // Save current thread and schedule next
        current_thread->state = READY;
        enqueue_thread(current_thread);
        
        // Switch to scheduler
        swapcontext(&current_thread->context, &scheduler_context);
    }
}

void mythread_yield(void) {
    if (current_thread && current_thread->state == RUNNING) {
        current_thread->state = READY;
        enqueue_thread(current_thread);
        
        swapcontext(&current_thread->context, &scheduler_context);
    }
}

// Scheduler function
static void scheduler(void) {
    while (1) {
        TCB* next_thread = dequeue_highest_priority_thread();
        
        if (next_thread) {
            TCB* prev_thread = current_thread;
            current_thread = next_thread;
            current_thread->state = RUNNING;
            
            if (prev_thread && prev_thread->state == RUNNING) {
                prev_thread->state = READY;
                enqueue_thread(prev_thread);
            }
            
            // Context switch to the selected thread
            setcontext(&current_thread->context);
        } else {
            pause();
        }
    }
}

// Initialize the thread library
void mythread_init(void) {
    if (scheduler_initialized) return;
    
    // Setup signal handler for timer interrupts
    struct sigaction sa;
    sa.sa_handler = timer_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    sigaction(SIGVTALRM, &sa, NULL);
    
    // Configure timer for preemptive scheduling
    timer.it_value.tv_sec = 0;
    timer.it_value.tv_usec = 10000;  // 10ms quantum
    timer.it_interval.tv_sec = 0;
    timer.it_interval.tv_usec = 10000;
    
    setitimer(ITIMER_VIRTUAL, &timer, NULL);
    
    // Create scheduler context
    getcontext(&scheduler_context);
    scheduler_context.uc_stack.ss_sp = malloc(SIGSTKSZ);
    scheduler_context.uc_stack.ss_size = SIGSTKSZ;
    scheduler_context.uc_link = NULL;
    makecontext(&scheduler_context, scheduler, 0);
    
    scheduler_initialized = true;
}

// Create a new thread
int mythread_create(int (*func)(void*), void* arg, ThreadPriority priority) {
    if (!scheduler_initialized) {
        mythread_init();
    }
    
    TCB* new_thread = (TCB*)malloc(sizeof(TCB));
    if (!new_thread) return -1;
    
    // Initialize thread context
    getcontext(&new_thread->context);
    new_thread->context.uc_stack.ss_sp = malloc(8192);
    new_thread->context.uc_stack.ss_size = 8192;
    new_thread->context.uc_link = &scheduler_context;
    
    // Set up thread function
    makecontext(&new_thread->context, (void(*)())func, 1, arg);
    
    // Initialize TCB fields
    new_thread->tid = next_tid++;
    new_thread->state = READY;
    new_thread->priority = priority;
    new_thread->return_value = NULL;
    new_thread->waiting_for = NULL;
    new_thread->joined = false;
    new_thread->join_list = NULL;
    new_thread->stack = new_thread->context.uc_stack.ss_sp;
    
    // Add to global thread list
    new_thread->next = all_threads;
    all_threads = new_thread;
    
    // Add to ready queue
    enqueue_thread(new_thread);
    
    return new_thread->tid;
}

// Get current thread ID
int mythread_self(void) {
    return current_thread ? current_thread->tid : 0;
}

// Exit current thread
void mythread_exit(void* retval) {
    if (!current_thread) return;
    
    current_thread->return_value = retval;
    current_thread->state = TERMINATED;
    
    // Wake up threads waiting on this thread
    TCB* waiter = current_thread->join_list;
    while (waiter) {
        waiter->state = READY;
        enqueue_thread(waiter);
        waiter = waiter->next;
    }
    
    // Schedule next thread
    TCB* next = dequeue_highest_priority_thread();
    if (next) {
        current_thread = next;
        current_thread->state = RUNNING;
        setcontext(&current_thread->context);
    } else {
        // No more threads, exit program
        exit(0);
    }
}

// Join a thread
int mythread_join(int tid, void** retval) {
    if (!current_thread) return -1;
    
    // Find the thread to join
    TCB* target = NULL;
    TCB* curr = all_threads;
    while (curr) {
        if (curr->tid == tid) {
            target = curr;
            break;
        }
        curr = curr->next;
    }
    
    if (!target || target->state == TERMINATED) {
        return -1;
    }
    
    // Add current thread to target's join list
    current_thread->state = WAITING;
    current_thread->next = target->join_list;
    target->join_list = current_thread;
    
    // Switch to scheduler
    swapcontext(&current_thread->context, &scheduler_context);
    
    // When we resume, target has terminated
    if (retval) {
        *retval = target->return_value;
    }
    
    return 0;
}

// Mutex initialization
void mythread_mutex_init(mythread_mutex_t* mutex) {
    mutex->locked = false;
    mutex->owner = NULL;
    mutex->waiting_queue = NULL;
    mutex->original_priority = LOW;
    mutex->elevated_priority = LOW;
    mutex->lock_count = 0;
}

// Mutex lock with priority elevation
void mythread_mutex_lock(mythread_mutex_t* mutex) {
    if (!current_thread) return;
    
    if (!mutex->locked) {
        // Mutex is free, acquire it
        mutex->locked = true;
        mutex->owner = current_thread;
        mutex->original_priority = current_thread->priority;
        mutex->lock_count = 1;
    } else if (mutex->owner == current_thread) {
        // Recursive lock
        mutex->lock_count++;
    } else {
        // Mutex is held by another thread
        // Apply priority elevation if needed
        if (current_thread->priority > mutex->owner->priority) {
            // Elevate owner's priority
            mutex->elevated_priority = current_thread->priority;
            mutex->owner->priority = current_thread->priority;
            
            // Move owner to higher priority queue
            TCB* owner = mutex->owner;
            // Remove from current position
            // (In a full implementation, you'd need to search and remove)
            // For now, we'll just update the priority
            
            printf("Priority elevation: Thread %d elevated to priority %d\n",
                   owner->tid, current_thread->priority);
        }
        
        // Add current thread to mutex waiting queue
        current_thread->state = BLOCKED;
        current_thread->next = mutex->waiting_queue;
        mutex->waiting_queue = current_thread;
        
        // Switch to scheduler
        swapcontext(&current_thread->context, &scheduler_context);
    }
}

// Mutex unlock with priority restoration
void mythread_mutex_unlock(mythread_mutex_t* mutex) {
    if (!mutex->locked || mutex->owner != current_thread) {
        return;  // Error: not owned by calling thread
    }
    
    mutex->lock_count--;
    
    if (mutex->lock_count == 0) {
        // Restore original priority if it was elevated
        if (mutex->elevated_priority > mutex->original_priority) {
            current_thread->priority = mutex->original_priority;
            printf("Priority restored: Thread %d back to priority %d\n",
                   current_thread->tid, mutex->original_priority);
        }
        
        // Wake up one waiting thread if any
        if (mutex->waiting_queue) {
            TCB* waiter = mutex->waiting_queue;
            mutex->waiting_queue = waiter->next;
            waiter->state = READY;
            enqueue_thread(waiter);
            
            // Transfer ownership
            mutex->owner = waiter;
            mutex->original_priority = waiter->priority;
            mutex->elevated_priority = waiter->priority;
            mutex->lock_count = 1;
        } else {
            mutex->locked = false;
            mutex->owner = NULL;
        }
    }
}

// Set thread priority
void mythread_set_priority(int tid, ThreadPriority priority) {
    TCB* thread = all_threads;
    while (thread) {
        if (thread->tid == tid) {
            thread->priority = priority;
            break;
        }
        thread = thread->next;
    }
}

// Get thread priority
ThreadPriority mythread_get_priority(int tid) {
    TCB* thread = all_threads;
    while (thread) {
        if (thread->tid == tid) {
            return thread->priority;
        }
        thread = thread->next;
    }
    return LOW;
}

// Deadlock detection (called on SIGQUIT)
void detect_deadlock(void) {
    printf("\n=== Deadlock Detection Report ===\n");
    
    bool deadlock = false;
    TCB* thread = all_threads;
    
    while (thread) {
        if (thread->state == BLOCKED || thread->state == WAITING) {
            printf("Thread %d (priority %d) is blocked/waiting\n", 
                   thread->tid, thread->priority);
            deadlock = true;
        }
        thread = thread->next;
    }
    
    if (!deadlock) {
        printf("No deadlocks detected.\n");
    }
    
    printf("================================\n");
}

static void sigquit_handler(int sig) {
    detect_deadlock();
}