// mythreads.h - Header file
#ifndef MYTHREADS_H
#define MYTHREADS_H

#include <ucontext.h>
#include <signal.h>
#include <sys/time.h>
#include <stdbool.h>

// Thread states
typedef enum {
    READY,
    RUNNING,
    BLOCKED,
    WAITING,
    TERMINATED
} ThreadState;

// Thread priority levels
typedef enum {
    LOW = 0,
    MEDIUM = 1,
    HIGH = 2
} ThreadPriority;

// Thread Control Block
typedef struct ThreadControlBlock {
    int tid;
    ucontext_t context;
    ThreadState state;
    ThreadPriority priority;
    void* return_value;
    struct ThreadControlBlock* waiting_for;  // For join
    struct ThreadControlBlock* next;
    void* stack;
    bool joined;
    struct ThreadControlBlock* join_list;
} TCB;

// Mutex structure with priority elevation
typedef struct {
    bool locked;
    TCB* owner;
    TCB* waiting_queue;
    ThreadPriority original_priority;  // For priority elevation tracking
    ThreadPriority elevated_priority;  // Current elevated priority
    int lock_count;
} mythread_mutex_t;

// Function prototypes
// Thread management
int mythread_create(int (*func)(void*), void* arg, ThreadPriority priority);
void mythread_exit(void* retval);
int mythread_join(int tid, void** retval);
int mythread_self(void);

// Mutex operations
void mythread_mutex_init(mythread_mutex_t* mutex);
void mythread_mutex_lock(mythread_mutex_t* mutex);
void mythread_mutex_unlock(mythread_mutex_t* mutex);

// Scheduler control
void mythread_init(void);
void mythread_yield(void);

// Priority management
void mythread_set_priority(int tid, ThreadPriority priority);
ThreadPriority mythread_get_priority(int tid);

// Deadlock detection
void detect_deadlock(void);

#endif