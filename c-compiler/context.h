#pragma once

#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "../runtime/lib/stb_ds.h" // TODO: temp!

// - Unit Context
typedef struct StringMap StringMap;

typedef struct {
    StringMap* stringOffsets;
    size_t currentStringOffset;
    const char** strings;
} UnitContext;

extern UnitContext UnitContext_current;

size_t offsetForString(const char* str);
const char* stringSymbol(const char* str);

// - Function Context
typedef struct {
    size_t temporaryIndex;
} FunctionContext;

extern FunctionContext FunctionContext_current;