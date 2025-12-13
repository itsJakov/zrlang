#include <stdio.h>

#include "zre.h"

static Field fields[] = {
        { .name = "name", .type = kFieldTypeUInt64 }
};

static Method instanceMethods[] = {

};

Class School = {
        .name = "School",
        .super = NULL,
        .fields = {
                .len = 1,
                .fields = fields
        },
        .staticMethods = { 0 },
        .instanceMethods = {
                .len = 0,
                .methods = instanceMethods
        }
};