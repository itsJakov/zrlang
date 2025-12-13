#pragma once

#include <unistd.h>
#include <stdbool.h>

#define kFieldTypeStrongObject 0
#define kFieldTypeUnownedObject 1
#define kFieldTypeUInt64 2

// - Instance Fields
typedef struct {
    const char* name;
    uint64_t type;
} Field;

typedef struct {
    uint64_t len;
    Field* fields;
} FieldTable;

// - Methods
typedef void* MethodImpl;

typedef struct {
    const char* name;
    MethodImpl impl;
} Method;

typedef struct {
    uint64_t len;
    Method* methods;
} MethodTable;

// - Class / Object / Instance
typedef struct Class {
    const char* name;
    struct Class* super;

    FieldTable fields;
    MethodTable staticMethods;
    MethodTable instanceMethods;
} Class;

typedef struct {
    Class* cls;
    int64_t rc;
    uint64_t storage[];
} Instance;

// - API
extern Class RootObject;

Instance* zre_alloc(Class* cls);

void zre_retain(Instance* obj);
void zre_release(Instance* obj);

uint64_t zre_field_get(Instance* obj, const char* name);
void zre_field_set(Instance* obj, const char* name, uint64_t value);

MethodImpl zre_method_lookup(Class* cls, const char* name, bool required);
MethodImpl zre_method_super(Class* cls, const char* name);
MethodImpl zre_method_virtual(Instance* obj, const char* name);