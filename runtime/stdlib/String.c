#include "zre.h"
#include "zre_utils.h"

#include <stdlib.h>
#include <string.h>

ZRE_FIELD_PTR(cstr, char*)
ZRE_FIELD_PTR(isConstant, uint64_t)

static void initWithCStr(Instance* self, char* cstr) {
    set_cstr(self, cstr);
    set_isConstant(self, 1);
}

static void initWithCStrConstant(Instance* self, const char* cstr) {
    set_cstr(self, (char*)cstr); // I promise I won't touch cstr if isConstant == 1
    set_isConstant(self, 1);
}

static ZREString concat(Instance* self, Instance* other) {
    Instance* strB = zre_call(other, "toString");

    char* cstrA = get_cstr(self);
    char* cstrB = get_cstr(strB);

    size_t lenA = strlen(cstrA);
    size_t lenB = strlen(cstrB);

    char* concatenated = malloc(lenA + lenB + 1);
    memcpy(concatenated, cstrA, lenA);
    memcpy(concatenated + lenA, cstrB, lenB);
    concatenated[lenA + lenB] = '\0';

    Instance* result = zre_alloc(&String);
    zre_call(result, "initWithCStr", concatenated);
    return result;
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

static void hashInto(Instance* self, Instance* hasher) {
    char* cstr = get_cstr(self);
    zre_call(hasher, "combineRawBuffer", cstr, strlen(cstr));
}

static uint64_t isEqual(Instance* self, Instance* other) {
    if (self == other) return true;
    if (other->cls != &String) return false;

    char* cstrA = get_cstr(self);
    char* cstrB = get_cstr(other);
    return strcmp(cstrA, cstrB) == 0;
}

static Field fields[] = {
        { .name = "cstr", .type = kFieldTypeUInt64 },
        { .name = "isConstant", .type = kFieldTypeUInt64 }
};

static Method methods[] = {
        // - Overrides
        { "deinit", deinit },
        { "toString", toString },
        { "hashInto", hashInto },
        { "isEqual", isEqual },

        { "initWithCStr", initWithCStr },
        { "initWithCStrConstant", initWithCStrConstant },
        { "concat", concat }
};

Class String = {
        .name = "String",
        .super = &Object,
        .fields = { .len = 2, fields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 7, methods }
};