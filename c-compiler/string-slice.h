#pragma once

#include <stddef.h>
#include <stdint.h>

typedef struct {
    int64_t start;
    int64_t end;
} StringSlice;

#define SLICE_NULL (StringSlice){ -1, -1 }
#define stringSliceIsNull(slice) ((slice)->start < 0)