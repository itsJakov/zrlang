#pragma once

#define SUPPRESS_WARNINGS(code) \
    _Pragma("GCC diagnostic push") \
    _Pragma("GCC diagnostic ignored \"-Wdeprecated-non-prototype\"") \
    code \
    _Pragma("GCC diagnostic pop")

#define ZRE_FIELD_PTR(NAME, TYPE) \
    static inline TYPE get_ ##NAME (Instance* self) { \
        return (TYPE)zre_field_get_int(self, #NAME); \
    } \
    static inline void set_ ##NAME (Instance* self, TYPE value) { \
        zre_field_set_int(self, #NAME, (uint64_t)value); \
    }

#define ZRE_FIELD_OBJ(NAME) \
    static inline Instance* get_ ##NAME (Instance* self) { \
        return zre_field_get_obj(self, #NAME); \
    } \
    static inline void set_ ##NAME (Instance* self, Instance* value) { \
        zre_field_set_obj(self, #NAME, value); \
    }

#define zre_call_type(obj, name, return_type, ...) \
    SUPPRESS_WARNINGS( \
        ((return_type (*)())zre_method_virtual(obj, name))(obj, ##__VA_ARGS__) \
    )

#define zre_call(obj, name, ...) zre_call_type(obj, name, Instance*, ##__VA_ARGS__)

// - String utilities
#define zstr(s) zre_string_literal(s)
#define zstr_get(s) ((const char*)zre_field_get_obj(s, "cstr"))

// - Hashing utilities
uint64_t zre_hash(Instance* obj);