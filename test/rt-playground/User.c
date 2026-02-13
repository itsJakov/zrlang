#include <stdio.h>
#include <string.h>

#include "zre.h"
#include "zre_utils.h"

ZRE_CLASS_FIELD(username, ZREString)
ZRE_CLASS_FIELD(school, Instance*)

static void init(Instance* self) {
    set_username(self, zstr("EmptyUser"));
}

static void greet(Instance* self, ZREString greeting) {
    printf("%s, %s!\n", zstr_get(greeting), zstr_get(get_username(self)));
}

static void testClass(Instance* self) {
    printf("+++ Testing class User (subclass: %s) +++\n", self->cls->name);
    printf("Username: %s\n", zstr_get(get_username(self)));
    printf("\tTesting greet(\"Greetings\")\n");
    zre_call(self, "greet", zstr("Greetings"));
    printf("+++ All done! +++\n");
}

static void hashInto(Instance* self, Instance* hasher) {
    zre_call(hasher, "combine", get_username(self));
    zre_call(hasher, "combine", get_school(self));
}

static Field fields[] = {
        { .name = "username", .type = kFieldTypeStrongObject },
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
        .super = &Object,
        .fields = { .len = 2, fields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 4, instanceMethods }
};