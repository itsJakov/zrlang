#include "zre.h"

#include "zre_utils.h"

#include <stdio.h>
#include <assert.h>

DEFINE_FIELD(handle, FILE*)

static void initWithPath(Instance* self, Instance* path) {
    const char* path_str = zstr_buf(path);
    FILE* file = fopen(path_str, "a+");
    if (file == NULL) {
        fprintf(stderr, "Failed to open file: %s\n", path_str);
        assert(0);
    }
    set_handle(self, file);
}

static void append(Instance* self, Instance* string) {
    FILE* file = get_handle(self);
    char* cstr = (char*)zre_field_get(string, "cstr");
    fprintf(file, "%s", cstr);
}

// - Overrides
static void deinit(Instance* self) {
    FILE *file = get_handle(self);
    fclose(file);
}

static Field fields[] = {
        { .name = "handle", .type = kFieldTypeUInt64 }
};

static Method methods[] = {
        // - Overrides
        { "deinit", deinit },

        { "initWithPath", initWithPath },
        { "append", append }
};

Class File = {
        .name = "File",
        .super = &RootObject,
        .fields = { .len = 1, fields },
        .staticMethods = { 0 },
        .instanceMethods = { .len = 3, methods }
};