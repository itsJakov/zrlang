#include <stdio.h>

#include "zre.h"

static void init(Instance* self) {
    zre_field_set(self, "username", (uint64_t)"EmptyUser");
}

static void greet(Instance* self, char* greeting) {
    printf("%s, %s!\n", greeting, (char*)zre_field_get(self, "username"));
}

static void testClass(Instance* self) {
    printf("Testing class User (subclass: %s)\n", self->cls->name);
    printf("\tTesting greet(\"Greetings\")\n");
    ((void (*)(Instance*, char*))zre_method_virtual(self, "greet"))(self, "Greetings");
    printf("All done!\n");
}

static Field fields[] = {
        { .name = "username", .type = kFieldTypeUInt64 },
        { .name = "school", .type = kFieldTypeStrongObject }
};

static Method instanceMethods[] = {
        { .name = "init", .impl = init },
        { .name = "greet", .impl = greet },
        { .name = "testClass", .impl = testClass }
};

Class User = {
        .name = "User",
        .super = &RootObject,
        .fields = {
                .len = 2,
                .fields = fields
        },
        .staticMethods = { 0 },
        .instanceMethods = {
                .len = 3,
                .methods = instanceMethods
        }
};