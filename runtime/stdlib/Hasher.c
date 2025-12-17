#include "zre.h"
#include "zre_utils.h"

#include "xxhash.h"

typedef XXH64_state_t HasherState;

DEFINE_FIELD(state, HasherState*)

static void init(Instance* self) {
    HasherState* state = XXH64_createState();
    set_state(self, state);

    XXH64_reset(state, 0);
}

static void deinit(Instance* self) {
    XXH64_freeState(get_state(self));
}

static void combine(Instance* self, Instance* obj) {
    if (obj == NULL) return;
    ((void (*)(Instance*, Instance*))zre_method_virtual(obj, "hashInto"))(obj, self);
}

static void combineInteger(Instance* self, uint64_t integer) {
    XXH64_update(get_state(self), &integer, sizeof(integer));
}

static void combineRawBuffer(Instance* self, void* buffer, uint64_t len) {
    XXH64_update(get_state(self), buffer, len);
}

static uint64_t finalize(Instance* self) {
    return XXH64_digest(get_state(self));
}

static Field fields[] = {
        { "state", kFieldTypeUInt64 }
};

static Method instanceMethods[] = {
        { "init", init },
        { "deinit", deinit },
        { "combine", combine },
        { "combineInteger", combineInteger },
        { "combineRawBuffer", combineRawBuffer },
        { "finalize", finalize },
};

Class Hasher = {
        .name = "Hasher",
        .super = &RootObject,
        .fields = { .len = 1, fields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 6, instanceMethods}
};