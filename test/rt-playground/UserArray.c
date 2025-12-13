#include <stdio.h>
#include <assert.h>

#include "zre.h"

#define INITIAL_CAPACITY 128

extern Class RawBuffer;

static void init(Instance* self) {
    zre_field_set(self, "count", 0);

    Instance* buffer = zre_alloc(&RawBuffer);
    ((void (*)(Instance*, uint64_t))zre_method_virtual(buffer, "initWithSize"))(buffer, INITIAL_CAPACITY);
    zre_field_set(self, "buffer", (uint64_t)buffer);
}

static void deinit(Instance* self) {
    uint64_t count = zre_field_get(self, "count");
    Instance* buffer = (Instance*)zre_field_get(self, "buffer");

    for (int i = 0; i < count; i++) {
        Instance* obj = ((Instance* (*)(Instance*, uint64_t))zre_method_virtual(buffer, "get"))(buffer, i);
        zre_release(obj);
    }
}

static Instance* get(Instance* self, uint64_t index) {
    Instance* buffer = (Instance*)zre_field_get(self, "buffer");

    uint64_t size = zre_field_get(buffer, "size");
    if (index >= size) {
        printf("[zre] Array (index = %llu, size = %llu) out of bounds!\n", index, size);
        assert(0);
        return 0;
    }

    Instance* item = (Instance*)((uint64_t (*)(Instance*, uint64_t))zre_method_virtual(buffer, "get"))(buffer, index);

    zre_retain(item); // [ARC] Methods returning objects need to return them retained
    return item;
}

static void append(Instance* self, Instance* item) {
    uint64_t count = zre_field_get(self, "count");

    Instance* buffer = (Instance*)zre_field_get(self, "buffer");
    uint64_t bufferSize = zre_field_get(buffer, "size");

    if (count > bufferSize) {
        bufferSize *= 2;
        ((void (*)(Instance*, uint64_t))zre_method_virtual(buffer, "resize"))(buffer, bufferSize);
    }

    zre_retain(item);
    ((void (*)(Instance*, uint64_t, uint64_t))zre_method_virtual(buffer, "set"))(buffer, count, (uint64_t)item);
    zre_field_set(self, "count", count+1);
}

static Field fields[] = {
        { "count", kFieldTypeUInt64 },
        { "buffer", kFieldTypeStrongObject }
};

static Method methods[] = {
        { "init", init },
        { "deinit", deinit },
        { "get", get },
        { "append", append }
};

Class UserArray = {
        .name = "UserArray",
        .super = &RootObject,
        .fields = { .len = 2, .fields = fields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 4, .methods = methods }
};