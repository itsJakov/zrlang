#include "zre.h"

#include <stdio.h>
#include <stdlib.h>

extern Class String;

static void deinit(Instance* self) {

}

static Instance* toString(Instance* self) {
    char* buffer = malloc(1024);
    snprintf(buffer, 1024, "%s <%p>", self->cls->name, self);

    Instance* string = zre_alloc(&String);
    ((void (*)(Instance*, char*))zre_method_virtual(string, "initWithCStr"))(string, buffer);
    return string;
}

static uint64_t hashInto(Instance* self, Instance* hasher) {
    ((void (*)(Instance*, uint64_t))zre_method_virtual(hasher, "combineInteger"))(hasher, (uint64_t)self);
}

static Method methods[] = {
        { "deinit", deinit },
        { "toString", toString },
        { "hashInto", hashInto }
};

Class RootObject = {
        .name = "Object",
        .super = NULL,
        .fields = { 0 },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 3, .methods = methods }
};