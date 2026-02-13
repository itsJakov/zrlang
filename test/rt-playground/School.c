#include "zre.h"

static Field fields[] = {
        { .name = "name", .type = kFieldTypeStrongObject }
};

Class School = {
        .name = "School",
        .super = &Object,
        .fields = {  .len = 1, fields },
        .staticMethods = { 0 },
        .instanceMethods = { 0 }
};