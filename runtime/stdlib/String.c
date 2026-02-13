#include "zre.h"
#include "zre_utils.h"

#include <stdlib.h>

ZRE_CLASS_FIELD(cstr, char*)
ZRE_CLASS_FIELD(isConstant, uint64_t)

static void initWithCStr(Instance* self, char* cstr) {
    set_cstr(self, cstr);
    set_isConstant(self, 1);
}

static void initWithCStrConstant(Instance* self, const char* cstr) {
    set_cstr(self, (char*)cstr); // I promise I won't touch cstr if isConstant == 1
    set_isConstant(self, 1);
}

// - Overrides
static void deinit(Instance* self) {
    if (get_isConstant(self) == 0) {
        free(get_cstr(self));
    }
}

static Instance* toString(Instance* self) {
    zre_retain(self); // [ARC] Methods returning objects need to return them retained
    return self;
}

static Field fields[] = {
        { .name = "cstr", .type = kFieldTypeUInt64 },
        { .name = "isConstant", .type = kFieldTypeUInt64 }
};

static Method methods[] = {
        // - Overrides
        { "deinit", deinit },
        { "toString", toString },

        { "initWithCStr", initWithCStr },
        { "initWithCStrConstant", initWithCStrConstant },
};

Class String = {
        .name = "String",
        .super = &Object,
        .fields = { .len = 2, fields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 4, methods }
};