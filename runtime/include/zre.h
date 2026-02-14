#pragma once

#include <stdint.h>
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
extern Class Object;

Instance* zre_alloc(Class* cls);

void zre_retain(Instance* obj);
void zre_release(Instance* obj);

uint64_t* zre_field_storage(Instance* obj, const char* name);

// - Convenience getters/setters for common types
// TODO: Because of stupid casting, it's not guaranteed that these functions act the same as zre_field_storage
bool zre_field_get_bool(Instance* obj, const char* name);
uint64_t zre_field_get_int(Instance* obj, const char* name);
Instance* zre_field_get_obj(Instance* obj, const char* name) ;
void zre_field_set_bool(Instance* obj, const char* name, bool value);
void zre_field_set_int(Instance* obj, const char* name, uint64_t value);
void zre_field_set_obj(Instance* obj, const char* name, Instance* value);

#define zre_field_set(obj, name, value) \
    _Generic((value), \
        bool: zre_field_set_bool, \
        Instance*: zre_field_set_obj, \
        default: zre_field_set_int \
    )((obj), (name), (value))

MethodImpl zre_method_lookup(Class* cls, const char* name, bool required);
MethodImpl zre_method_super(Class* cls, const char* name);
MethodImpl zre_method_virtual(Instance* obj, const char* name);

extern Class String;
typedef Instance* ZREString;
ZREString zre_string_literal(const char* s);
ZREString zre_string(char* s);
void zre_print(Instance* obj);
