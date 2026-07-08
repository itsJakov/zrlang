#include "zre.h"
#include "zre_utils.h"

ZRE_FIELD_OBJ(array)
ZRE_FIELD_PTR(idx, uint64_t)

static void initWithArray(Instance* self, Instance* array) {
    set_array(self, array);
    set_idx(self, 0);
}

static bool hasNext(Instance* self) {
    Instance* array = get_array(self);
    uint64_t idx = get_idx(self);

    uint64_t count = zre_call_type(array, "getCount", uint64_t, array);
    return idx < count;
}

static Instance* next(Instance* self) {
    Instance* array = get_array(self);
    uint64_t idx = get_idx(self);

    Instance* item = zre_call(array, "get", idx);
    set_idx(self, idx + 1);
    return item;
}

static Field fields[] = {
        { "array", kFieldTypeStrongObject },
        { "idx", kFieldTypeUInt64 }
};

static Method instanceMethods[] = {
        { "initWithArray", initWithArray },
        { "hasNext", hasNext },
        { "next", next }
};

Class ArrayIterator = {
        .name = "_ArrayIterator",
        .super = &Object,
        .fields = { .len = 2, fields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 3, instanceMethods }
};