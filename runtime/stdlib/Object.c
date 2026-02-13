#include "zre.h"

#include <stdio.h>
#include <stdlib.h>

static void deinit(Instance* self) {}

static ZREString toString(Instance* self) {
    char* buffer = malloc(1024);
    snprintf(buffer, 1024, "%s <%p>", self->cls->name, self);
    return zre_string(buffer);
}

static void hashInto(Instance* self, Instance* hasher) {
    ((void (*)(Instance*, uint64_t))zre_method_virtual(hasher, "combineInteger"))(hasher, (uint64_t)self);
}

static Method methods[] = {
        { "deinit", deinit },
        { "toString", toString },
        { "hashInto", hashInto }
};

Class Object = {
        .name = "Object",
        .super = NULL,
        .fields = { 0 },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 3, methods }
};