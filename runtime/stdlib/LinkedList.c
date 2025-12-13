#include "zre.h"


// - Linked List Node
static void node_init(Instance* self) {
    zre_field_set(self, "obj", 0);
}

static Field nodeFields[] = {
        { "obj", kFieldTypeStrongObject },
        { "next", kFieldTypeStrongObject }
};

static Method nodeMethods[] = {
        { "init", node_init }
};

Class Node = {
        .name = "_LinkedListNode",
        .super = &RootObject,
        .fields = { .len = 1, .fields = nodeFields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 1, .methods = nodeMethods }
};
// -

static void init(Instance* self) {
    zre_field_set(self, "root", 0);
}

static void add(Instance* self, Instance* obj) {
    Instance* node = zre_alloc(&Node);
    zre_field_set(node, "obj", (uint64_t)obj);
    zre_retain(obj); // [ARC]

    // TODO: lmao
}

static Field fields[] = {
        { "root", kFieldTypeStrongObject }
};

static Method methods[] = {
        { "init", init },
        { "add", add }
};

Class LinkedList = {
        .name = "LinkedList",
        .super = &RootObject,
        .fields = { 0 },
        .staticMethods = { 0 },
        .instanceMethods = { 0 }
};