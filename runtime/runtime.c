#include "zre.h"

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>

//#define ARC_DEBUG
#define ALLOC_DEBUG

static size_t getStorageSize(Class* cls) {
    size_t size = 0;
    Class* current = cls;
    while (current != NULL) {
        size += current->fields.len * sizeof(uint64_t);
        current = current->super;
    }
    return size;
}

Instance* zre_alloc(Class* cls) {
    size_t storageSize = getStorageSize(cls);
    Instance* obj = malloc(sizeof(Instance) + storageSize);
    memset(obj->storage, 0, storageSize); // Might not be necessary
    obj->cls = cls;
    obj->rc = 1;

#ifdef ALLOC_DEBUG
    printf("[zre] Allocating %s <%p> (rc=%lld)\n", obj->cls->name, obj, obj->rc);
#endif
    return obj;
}

void zre_retain(Instance* obj) {
    if (obj == NULL) return;
    obj->rc++;
#ifdef ARC_DEBUG
    printf("[zre] Retain %s <%p> (rc=%lld)\n", obj->cls->name, obj, obj->rc);
#endif
}

void zre_release(Instance* obj) {
    if (obj == NULL) return;
    obj->rc--;

#ifdef ARC_DEBUG
    printf("[zre] Release %s <%p> (rc=%lld)\n", obj->cls->name, obj, obj->rc);
#endif

    if (obj->rc <= 0) {
        void(* deinitFn)(Instance*) = zre_method_lookup(obj->cls, "deinit", false);
        if (deinitFn != NULL) {
            deinitFn(obj);
        }

        Class* currentCls = obj->cls;
        size_t offset = 0;
        while (currentCls != NULL) {
            for (int i = 0; i < currentCls->fields.len; i++) {
                Field* field = &currentCls->fields.fields[i];
                if (field->type == kFieldTypeStrongObject) {
                    Instance* refObj = (Instance*)obj->storage[offset + 1];
                    zre_release(refObj);
                }
            }

            offset += currentCls->fields.len;
            currentCls = currentCls->super;
        }

#ifdef ALLOC_DEBUG
        printf("[zre] Freeing %s <%p>\n", obj->cls->name, obj);
#endif
        free(obj);
    }
}

static uint64_t* storageForField(Instance* obj, const char* name) {
    Class* currentCls = obj->cls;
    size_t offset = 0;
    while (currentCls != NULL) {
        for (int i = 0; i < currentCls->fields.len; i++) {
            Field* field = &currentCls->fields.fields[i];
            if (strcmp(name, field->name) == 0) {
                return &obj->storage[offset + i];
            }
        }

        offset += currentCls->fields.len;
        currentCls = currentCls->super;
    }

    fprintf(stderr, "[zre] No field named \"%s\" on type %s!\n", name, obj->cls->name);
    assert(0);
    return NULL;
}

uint64_t zre_field_get(Instance* obj, const char* name) {
    uint64_t* fieldStorage = storageForField(obj, name);
    return *fieldStorage;
}

void zre_field_set(Instance* obj, const char* name, uint64_t value) {
    uint64_t* fieldStorage = storageForField(obj, name);
    *fieldStorage = value; // TODO: Should this retain kFieldTypeStrongObject?
}

MethodImpl zre_method_lookup(Class* cls, const char* name, bool required) {
    Class* current = cls;
    while (current != NULL) {
        for (int i = 0; i < current->instanceMethods.len; i++) {
            Method* method = &current->instanceMethods.methods[i];
            if (strcmp(name, method->name) == 0) {
                return method->impl;
            }
        }

        current = current->super;
    }

    if (required) {
        fprintf(stderr, "[zre] Cannot find method named \"%s\" in class %s!\n", name, cls->name);
        assert(0);
    }
    return NULL;
}

MethodImpl zre_method_super(Class* cls, const char* name) {
    return zre_method_lookup(cls, name, true);
}

MethodImpl zre_method_virtual(Instance* obj, const char* name) {
    return zre_method_lookup(obj->cls, name, true);
}