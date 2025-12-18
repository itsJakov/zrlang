#include <stdio.h>
#include <string.h>

#include "zre.h"
#include "zre_utils.h"

DEFINE_FIELD(username, char*)
DEFINE_FIELD(school, Instance*)

static void init(Instance* self) {
    set_username(self, "EmptyUser");
}

static void greet(Instance* self, char* greeting) {
    printf("%s, %s!\n", greeting, get_username(self));
}

static void testClass(Instance* self) {
    printf("Testing class User (subclass: %s)\n", self->cls->name);
    printf("Username: %s\n", (char*)zre_field_get(self, "username"));
    printf("\tTesting greet(\"Greetings\")\n");
    ((void (*)(Instance*, char*))zre_method_virtual(self, "greet"))(self, "Greetings");
    printf("All done!\n");
}

static void hashInto(Instance* self, Instance* hasher) {
    char* username = get_username(self);
    ((void (*)(Instance*, void*, uint64_t))zre_method_virtual(hasher, "combineRawBuffer"))(hasher, username, strlen(username));

    ((void (*)(Instance*, Instance*))zre_method_virtual(hasher, "combine"))(hasher, get_school(self));
}

static Field fields[] = {
        { .name = "username", .type = kFieldTypeUInt64 },
        { .name = "school", .type = kFieldTypeStrongObject }
};

static Method instanceMethods[] = {
        { .name = "init", .impl = init },
        { .name = "greet", .impl = greet },
        { .name = "testClass", .impl = testClass },
        { .name = "hashInto", .impl = hashInto }
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
                .len = 4,
                .methods = instanceMethods
        }
};