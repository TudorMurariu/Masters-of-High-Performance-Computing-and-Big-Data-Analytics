// priority_test.c - Tests thread priorities without mutexes
#include "mythreads.h"
#include <stdio.h>
#include <signal.h>

// Global counters to track execution
int high_count = 0;
int medium_count = 0;
int low_count = 0;
int main_count = 0;

void handle_sigquit(int sig) {
    (void)sig;
    detect_deadlock();
}

int high_priority_thread(void* arg) {
    int id = *(int*)arg;
    int my_id = mythread_self();
    printf("HIGH Thread %d (TID %d): Starting - should run MOST often\n", id, my_id);
    
    for (int i = 0; i < 10; i++) {
        high_count++;
        printf("HIGH Thread %d: Execution %d (total HIGH runs: %d)\n", id, i+1, high_count);
        mythread_yield();
    }
    
    printf("HIGH Thread %d: Finished with %d total executions\n", id, high_count);
    mythread_exit((void*)(long)high_count);
    return 0;
}
int medium_priority_thread(void* arg) {
    int id = *(int*)arg;
    int my_id = mythread_self();
    printf("MEDIUM Thread %d (TID %d): Starting - should run LESS than high priority\n", id, my_id);
    
    for (int i = 0; i < 10; i++) {
        medium_count++;
        printf("MEDIUM Thread %d: Execution %d (total MEDIUM runs: %d)\n", id, i+1, medium_count);
        mythread_yield();
    }
    
    printf("MEDIUM Thread %d: Finished with %d total executions\n", id, medium_count);
    mythread_exit((void*)(long)medium_count);
    return 0;
}

int low_priority_thread(void* arg) {
    int id = *(int*)arg;
    int my_id = mythread_self();
    printf("LOW Thread %d (TID %d): Starting - should run LEAST often\n", id, my_id);
    
    for (int i = 0; i < 10; i++) {
        low_count++;
        printf("LOW Thread %d: Execution %d (total LOW runs: %d)\n", id, i+1, low_count);
        mythread_yield();
    }
    
    printf("LOW Thread %d: Finished with %d total executions\n", id, low_count);
    mythread_exit((void*)(long)low_count);
    return 0;
}

int main() {
    printf("=== PURE PRIORITY SCHEDULING TEST ===\n");
    printf("Testing scheduler behavior WITHOUT mutexes\n");
    printf("Higher priority threads should get more CPU time\n\n");
    
    signal(SIGQUIT, handle_sigquit);
    
    printf("Main thread ID: %d\n", mythread_self());
    
    // Create threads with different priorities
    printf("\nCreating threads with different priorities:\n");
    
    printf("1. Creating LOW priority thread (priority 0)\n");
    int tid_low = mythread_create(low_priority_thread, &(int){1}, LOW);
    printf("   Low thread TID: %d\n", tid_low);
    
    printf("2. Creating MEDIUM priority thread (priority 1)\n");
    int tid_medium = mythread_create(medium_priority_thread, &(int){2}, MEDIUM);
    printf("   Medium thread TID: %d\n", tid_medium);
    
    printf("3. Creating HIGH priority thread (priority 2)\n");
    int tid_high = mythread_create(high_priority_thread, &(int){3}, HIGH);
    printf("   High thread TID: %d\n", tid_high);
    
    printf("\nExpected behavior:\n");
    printf("- HIGH priority thread should run most frequently\n");
    printf("- MEDIUM priority thread should run less than HIGH\n");
    printf("- LOW priority thread should run least frequently\n");
    printf("- Main thread (MEDIUM priority) should also get some time\n");
    printf("\nStarting execution with 40 yields from main thread...\n");
    printf("=====================================================\n\n");
    
    // Main thread also yields to show it gets time too
    for (int i = 0; i < 40; i++) {
        main_count++;
        printf("MAIN: Yield %d (Main executed %d times)\n", i+1, main_count);
        mythread_yield();
    }
    
    // Print final statistics
    printf("\n=== FINAL STATISTICS ===\n");
    printf("HIGH priority thread executions:   %d\n", high_count);
    printf("MEDIUM priority thread executions: %d\n", medium_count);
    printf("LOW priority thread executions:    %d\n", low_count);
    printf("MAIN thread executions:            %d\n", main_count);
    printf("Total executions:                  %d\n", 
           high_count + medium_count + low_count + main_count);
    
    // Calculate ratios
    if (low_count > 0) {
        printf("\nExecution ratios (relative to LOW priority):\n");
        printf("HIGH/LOW ratio:   %.2f\n", (float)high_count / low_count);
        printf("MEDIUM/LOW ratio: %.2f\n", (float)medium_count / low_count);
        printf("MAIN/LOW ratio:   %.2f\n", (float)main_count / low_count);
    }
    
    printf("\nExpected: HIGH count > MEDIUM count > LOW count\n");
    
    return 0;
}