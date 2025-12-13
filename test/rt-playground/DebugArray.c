#include <stdio.h>

#include "zre.h"

extern Class Array;
extern Class DebugArray;

static void append(Instance* self, Instance* item) {
    printf("DebugArray appended item!\n");

    // super.append(item)
    ((void (*)(Instance*, Instance*)) zre_method_super(DebugArray.super, "append"))(self, item);
}

static Method methods[] = {
        { "append", append }
};

Class DebugArray = {
        .name = "DebugArray",
        .super = &Array,
        .instanceMethods = {
                .len = 1,
                .methods = methods
        }
};