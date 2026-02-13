#include "zre.h"
#include "zre_utils.h"

#include <stdio.h>
#include <stdlib.h>

static void deinit(Instance* self) {}

static ZREString toString(Instance* self) {
    char* buffer = malloc(1024);
    snprintf(buffer, 1024, "%s <%p>", self->cls->name, self);
    return zre_string(buffer);
}

static uint64_t isEqual(Instance* self, Instance* other) {
    return self == other;
}

static void hashInto(Instance* self, Instance* hasher) {
    zre_call(hasher, "combineInteger", (uint64_t)self);
}

static Method methods[] = {
        { "deinit", deinit },
        { "toString", toString },
        { "isEqual", isEqual },
        { "hashInto", hashInto }
};

Class Object = {
        .name = "Object",
        .super = NULL,
        .fields = { 0 },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 4, methods }
};