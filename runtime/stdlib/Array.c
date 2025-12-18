#include <assert.h>
#include <stdio.h>

#include "zre.h"
#include "zre_utils.h"
#include "stb_ds.h"

DEFINE_FIELD(array, Instance**)

static void init(Instance* self) {
    zre_field_set(self, "array", 0);
}

static void deinit(Instance* self) {
    Instance** array = get_array(self);
    for (int i = 0; i < arrlen(array); i++) {
        zre_release(array[i]);
    }

    arrfree(array);
}

static Instance* get(Instance* self, uint64_t index) {
    Instance** array = get_array(self);
    size_t len = arrlenu(array);
    if (index >= len) {
        printf("[zre] Array (count = %lu) out of bounds!\n", len);
        assert(0);
        return NULL;
    }

    Instance* item = array[index];
    zre_retain(item); // [ARC] Methods returning objects need to return them retained
    return item;
}

static uint64_t getCount(Instance* self) {
    Instance** array = get_array(self);
    return arrlenu(array);
}

static uint64_t getIsEmpty(Instance* self) {
    Instance** array = get_array(self);
    return arrlenu(array) <= 0;
}

static void append(Instance* self, Instance* item) {
    Instance** array = get_array(self);

    zre_retain(item);
    arrput(array, item);
    set_array(self, array);
}

static Field fields[] = {
    { "array", kFieldTypeUInt64 }
};

static Method instanceMethods[] = {
    { "init", init },
    { "deinit", deinit },
    { "get", get },
    { "getCount", getCount },
    { "getIsEmpty", getIsEmpty },
    { "append", append },
};

Class Array = {
    .name = "Array",
    .super = &RootObject,
    .fields = { .len = 1, fields },
    .staticMethods = { 0 },
    .instanceMethods = { .len = 6, instanceMethods }
};