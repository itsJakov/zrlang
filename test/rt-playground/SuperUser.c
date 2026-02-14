#include <stdio.h>

#include "zre.h"

extern Class SuperUser;

static void greet(Instance* self, char* greeting) {

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