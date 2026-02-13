#include "zre.h"
#include "zre_utils.h"

uint64_t zre_hash(Instance* obj) {
    extern Class Hasher;
    Instance* hasher = zre_alloc(&Hasher);
    zre_call(hasher, "init");

    zre_call(obj, "hashInto", hasher);
    uint64_t hash = zre_call_type(hasher, "finalize", uint64_t, hasher);

    zre_release(hasher);
    return hash;
}

void _zr_print(Instance* obj) {
    zre_print(obj);
}