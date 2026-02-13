#include "zre.h"
#include "zre_utils.h"

#define REGISTER_ZMAP_TYPES(X) \
    X(Instance*, Instance*, ObjObj)

#include "zmap.h"

ZRE_CLASS_FIELD(map, zmap_ObjObj*)

static uint32_t hash_obj(Instance* obj, uint32_t seed) {
    uint64_t hash = zre_hash(obj);
    return ZMAP_HASH_SCALAR(hash, seed);
}

static int cmp_obj(Instance* a, Instance* b) {
    return zre_call_type(a, "isEqual", uint64_t, b) ? 0 : 1;
}

static void init(Instance* self) {
    // Because the runtime can only store exactly 64-bits per filed
    // the zmap structure is allocated on the heap (ugh...)
    zmap_ObjObj* map = malloc(sizeof(zmap_ObjObj));
    *map = zmap_init_ObjObj(hash_obj, cmp_obj);
    set_map(self, map);
}

static void deinit(Instance* self) {
    zmap_ObjObj* map = get_map(self);

    zmap_iter_ObjObj iter = zmap_iter_init_ObjObj(map);
    Instance* key;
    Instance* value;
    while (zmap_iter_next_ObjObj(&iter, &key, &value)) {
        zre_release(key);
        zre_release(value);
    }
    zmap_free(map);
    free(map);
}

static Instance* get(Instance* self, Instance* keyObj) {
    zmap_ObjObj* map = get_map(self);

    Instance** value = zmap_get(map, keyObj);
    if (value == NULL) return NULL;

    zre_retain(*value); // [ARC] Methods returning objects need to return them retained
    return *value;
}

static void set(Instance* self, Instance* keyObj, Instance* value) {
    zmap_ObjObj* map = get_map(self);

    zmap_put(map, keyObj, value);
    zre_retain(keyObj);
    zre_retain(value);
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
    .super = &Object,
    .fields = { .len = 1, fields },
    .staticMethods = { 0 },
    .instanceMethods = { .len = 4, instanceMethods }
};