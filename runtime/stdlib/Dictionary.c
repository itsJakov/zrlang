#include <stdio.h>

#include "zre.h"
#include "zre_utils.h"

#include "stb_ds.h"

typedef struct {
    uint64_t key;
    Instance* keyObj;
    Instance* value;
} Entry;

DEFINE_FIELD(map, Entry*)

static uint64_t get_hash(Instance* obj) {
    extern Class Hasher;
    Instance* hasher = zre_alloc(&Hasher);
    ((void (*)(Instance*))zre_method_virtual(hasher, "init"))(hasher);

    ((void (*)(Instance*, Instance*))zre_method_virtual(obj, "hashInto"))(obj, hasher);
    uint64_t hash = ((uint64_t (*)(Instance*))zre_method_virtual(hasher, "finalize"))(hasher);

    zre_release(hasher);
    return hash;
}

static void init(Instance* self) {

}

static void deinit(Instance* self) {
    Entry* map = get_map(self);
    for (int i = 0; i < hmlen(map); i++) {
        Entry* entry = &map[i];
        zre_release(entry->keyObj);
        zre_release(entry->value);
    }

    hmfree(map);
}

static Instance* get(Instance* self, Instance* keyObj) {
    Entry* map = get_map(self);

    Instance* value = hmget(map, get_hash(keyObj));
    zre_retain(value); // [ARC] Methods returning objects need to return them retained
    return value;
}

static void set(Instance* self, Instance* keyObj, Instance* value) {
    Entry* map = get_map(self);

    Entry newEntry = {
        .key = get_hash(keyObj),
        .keyObj = keyObj,
        .value = value
    };
    zre_retain(keyObj);
    zre_retain(value);

    hmputs(map, newEntry);
    set_map(self, map);
}

static Field fields[] = {
    { "map", kFieldTypeUInt64 }
};

static Method instanceMethods[] = {
    { "init", init },
    { "deinit", deinit },
    { "get", get },
    { "set", set }
};

Class Dictionary = {
    .name = "Dictionary",
    .super = &RootObject,
    .fields = { .len = 1, fields },
    .staticMethods = { 0 },
    .instanceMethods = { .len = 4, instanceMethods }
};