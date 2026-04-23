#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <errno.h>

void buffer_overflow_safe(char *input) {
    char buffer[10];
    snprintf(buffer, sizeof(buffer), "%s", input);
    printf("Buffer received: %s\n", buffer);
}

void integer_overflow_safe(char *input) {
    char *endptr;
    errno = 0;
    
    long count_long = strtol(input, &endptr, 10);
    
    // Check for conversion errors or negative allocations
    if (errno == ERANGE || count_long <= 0 || count_long > INT_MAX) {
        printf("Invalid input or integer out of bounds.\n");
        return;
    }
    
    int count = (int)count_long;
    int width = sizeof(int);
    
    if (count > INT_MAX / width) {
        printf("Requested size is too large (Integer Overflow prevented).\n");
        return;
    }
    
    int total = count * width;
    int *arr = malloc(total);

    if (!arr) {
        printf("Memory allocation failed.\n");
        return;
    }
    
    for (int i = 0; i < count; i++) {
        arr[i] = i;
    }

    printf("Allocated array of %d integers.\n", count);
    free(arr);
}

void format_string_safe(char *input) {
    printf("%s\n", input);
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: %s <overflow|int|format> <input>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "overflow") == 0) {
        buffer_overflow_safe(argv[2]);
    } else if (strcmp(argv[1], "int") == 0) {
        integer_overflow_safe(argv[2]);
    } else if (strcmp(argv[1], "format") == 0) {
        format_string_safe(argv[2]);
    } else {
        printf("Unknown option: %s\n", argv[1]);
        return 1;
    }

    return 0;
}