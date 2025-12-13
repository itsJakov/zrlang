#include <stdio.h>

#include "zre.h"

extern Class SuperUser;

static void greet(Instance* self, char* greeting) {
    printf("%s, '%s' %s!\n", greeting, (char*)zre_field_get(self, "title"), (char*)zre_field_get(self, "username"));
//    ((void (*)(Instance*, char*))zre_method_super(SuperUser.super, "greet"))(self, greeting);

}

static Field fields[] = {
        { .name = "title", .type = kFieldTypeUInt64 }
};

static Method methods[] = {
        { .name = "greet", .impl = greet }
};

extern Class User;

Class SuperUser = {
        .name = "SuperUser",
        .super = &User,
        .fields = {
                .len = 1,
                .fields = fields
        },
        .staticMethods = { 0 },
        .instanceMethods = {
                .len = 1,
                .methods = methods
        }
};