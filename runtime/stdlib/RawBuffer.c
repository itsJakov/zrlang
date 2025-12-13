#include "zre.h"

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

static void initWithSize(Instance* self, uint64_t size) {
    zre_field_set(self, "size", size);

    uint64_t* buffer = malloc(sizeof(uint64_t) * size);
    zre_field_set(self, "buffer", (uint64_t)buffer);
}

static void deinit(Instance* self) {
    uint64_t* buffer = (uint64_t*)zre_field_get(self, "buffer");
    free(buffer);
}

static uint64_t* ptrForIndex(Instance* self, uint64_t index) {
    uint64_t size = zre_field_get(self, "size");

    if (index >= size) {
        printf("[zre] RawBuffer (index = %llu, size = %llu) out of bounds!\n", index, size);
        assert(0);
        return 0;
    }

    uint64_t* buffer = (uint64_t*)zre_field_get(self, "buffer");
    return &buffer[index];
}

static uint64_t get(Instance* self, uint64_t index) {
    return *ptrForIndex(self, index);
}

static void set(Instance* self, uint64_t index, uint64_t value) {
    *ptrForIndex(self, index) = value;
}

static void resize(Instance* self, uint64_t newSize) {
    uint64_t* buffer = (uint64_t*)zre_field_get(self, "buffer");
    uint64_t* newBuffer = realloc(buffer, newSize);
    if (newBuffer == NULL) {
        printf("[zre] RawBuffer (newSize = %llu) unable to resize!\n", newSize);
        assert(0);
    }

    zre_field_set(self, "buffer", (uint64_t)newBuffer);
}

static Field fields[] = {
        { "size", kFieldTypeUInt64 },
        { "buffer", kFieldTypeUInt64 }
};

static Method methods[] = {
        { "initWithSize", initWithSize },
        { "deinit", deinit },
        { "get", get },
        { "set", set }
};

Class RawBuffer = {
        .name = "RawBuffer",
        .super = &RootObject,
        .fields = { .len = 2, .fields = fields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 4, .methods = methods }
};