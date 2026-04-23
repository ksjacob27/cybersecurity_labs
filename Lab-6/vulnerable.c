#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <limits.h>  // Required for integer limits

void overRun(void) {
    int *x = malloc(10 * sizeof(int));

    if (x == NULL) {return;}

    x[9] = 0;  // Buffer overrun
    free(x);
}

void randStringGen(int x, char* c) {
    srand(time(NULL));
    for (int i = 0; i < x - 1; ++i) {
        *c = 'A' + (rand() % 26);
        c++;
    }
    *c = '\0';
}

void bufferUnder(void) {
    char buffer[256];
    char *c = malloc(255 * sizeof(char));
    randStringGen(255, c);
    strcpy(buffer, c);  // Possible buffer overflow
    printf("%s\n", buffer);
    free(c);
}

void danglingPtr(void) {
    int *x;
    int *y = malloc(10 * sizeof(int));
    
    // Safety check for allocation
    if (y == NULL) {
        return;
    }

    x = y;

    //  Access the memory while it is still valid.
    // In the original code, the access happened AFTER the free.
    x[2] = 42; 
    int t = x[2]; 
    printf("Valid pointer value: %d\n", t);

    //  Free the memory only when you are completely finished with it.
    free(y); 

    //  Defensive Programming. 
    // Set pointers to NULL after freeing to prevent accidental "use-after-free".
    y = NULL;
    x = NULL; 
}


void unInitializedPtr(void) {
    char *buffer = malloc(10 * sizeof(char));
    if (buffer == NULL) {
        return;
    }

    char *c = malloc(10 * sizeof(char));
    if (c == NULL) {
        free(buffer);
        return;
    }

    randStringGen(10, c);

    // Now that 'buffer' points to a valid memory block, strcpy is safe.
    strcpy(buffer, c);

    printf("%s\n", buffer);
    free(c);
    free(buffer);
}
void bufferOver(void) {
    char buffer[256];
    char *c = malloc(260 * sizeof(char));
    randStringGen(260, c);
    strcpy(buffer, c);  // Buffer overflow
    printf("%s\n", buffer);
    free(c);
}

// New: Integer Overflow Vulnerability
void integerOverflow(void) {
    int a = INT_MAX;  // Max signed int value (typically 2,147,483,647)
    int b = 1;
    int result;

    //  Implement a boundary check before performing the addition.
    // We check if 'a' is greater than (INT_MAX - b). 
    // If it is, adding 'b' to 'a' will definitely cause an overflow.
    if (a > INT_MAX - b) {
        printf("Integer Overflow detected! Operation aborted to prevent undefined behavior.\n");
    } else {
        result = a + b;
        printf("Result: %d\n", result);
    }
}

int main(int argc, char**argv) {
    if (argc != 2) {
        return 0;
    }
    int x = atoi(argv[1]);  // Convert input to integer

    if (x == 1) {
        overRun();
    } else if (x == 2) {
        unInitializedPtr();
    } else if (x == 3) {
        danglingPtr();
    } else if (x == 4) {
        bufferUnder();
    } else if (x == 5) {
        bufferOver();
    } else if (x == 6) {
        integerOverflow();
    }

    return 0;
}
