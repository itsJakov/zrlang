#include "zre.h"


#include <stdio.h>
#include <stdlib.h>

static void initWithCStr(Instance* self, char* cstr) {
    zre_field_set(self, "cstr", (uint64_t)cstr);
    zre_field_set(self, "isConstant", 0);
}

static void initWithCStrConstant(Instance* self, const char* cstr) {
    zre_field_set(self, "cstr", (uint64_t)cstr);
    zre_field_set(self, "isConstant", 1);
}

static void printToStdout(Instance* self) {
    char* cstr = (char*)zre_field_get(self, "cstr");
    puts(cstr);
}

// - Overrides
static void deinit(Instance* self) {
    if (zre_field_get(self, "isConstant") == 0) {
        char* cstr = (char*)zre_field_get(self, "cstr");
        free(cstr);
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
//        { "toString", toString}

        { "initWithCStr", initWithCStr },
        { "initWithCStrConstant", initWithCStrConstant },
        { "printToStdout", printToStdout }
};

Class String = {
        .name = "String",
        .super = &RootObject,
        .fields = { .len = 2, .fields = fields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 4, .methods = methods }
};