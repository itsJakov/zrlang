#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#include "zre.h"

#define INITIAL_CAPACITY 128

static void init(Instance* self) {
    zre_field_set(self, "count", 0);
    zre_field_set(self, "capacity", INITIAL_CAPACITY);

    Instance** data = malloc(sizeof(Instance*) * INITIAL_CAPACITY);
    zre_field_set(self, "data", (uint64_t)data);
}

static void deinit(Instance* self) {
    uint64_t count = zre_field_get(self, "count");
    Instance** data = (Instance**)zre_field_get(self, "data");

    for (size_t i = 0; i < count; i++) {
        zre_release(data[i]);
    }
    free(data);
}

static Instance* get(Instance* self, uint64_t index) {
    uint64_t count = zre_field_get(self, "count");
    if (index >= count) {
        printf("[zre] Array (size = %llu) out of bounds!\n", count);
        assert(0);
        return NULL;
    }

    Instance** data = (Instance**)zre_field_get(self, "data");

    Instance* obj = data[index];
    zre_retain(obj); // [ARC] Methods returning objects need to return them retained
    return obj;
}

static void append(Instance* self, Instance* item) {
    uint64_t count = zre_field_get(self, "count");
    uint64_t capacity = zre_field_get(self, "capacity");
    Instance** data = (Instance**)zre_field_get(self, "data");

    if (count > capacity) {
        capacity *= 2;
        zre_field_set(self, "capacity", capacity);

        Instance** newData = realloc(data, capacity);
        if (newData == NULL) {
            printf("[zre] Array (capacity = %llu) unable to grow!\n", count);
            assert(0);
        }
        zre_field_set(self, "data", (uint64_t)newData);
    }

    zre_retain(item); // [ARC]
    data[count] = item;
    zre_field_set(self, "count", count+1);
}

static Field fields[] = {
        { .name = "data", .type = kFieldTypeUInt64 },
        { .name = "count", .type = kFieldTypeUInt64 },
        { .name = "capacity", .type = kFieldTypeUInt64 }
};

static Method instanceMethods[] = {
        { .name = "init", .impl = init },
        { .name = "deinit", .impl = deinit },
        { .name = "get", .impl = get },
        { .name = "append", .impl = append },
};

Class Array = {
        .name = "Array",
        .super = NULL,
        .fields = {
                .len = 3,
                .fields = fields
        },
        .staticMethods = { 0 },
        .instanceMethods = {
                .len = 4,
                .methods = instanceMethods
        }
};