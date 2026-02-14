#pragma once

#if defined(__clang__)
#define SUPPRESS_WARNINGS(code) \
    _Pragma("clang diagnostic push") \
    _Pragma("clang diagnostic ignored \"-Wdeprecated-non-prototype\"") \
    code \
    _Pragma("clang diagnostic pop")
#else
// suprisingly GCC doesn't warn on this by default
#define SUPPRESS_WARNINGS(code) code
#endif

#define ZRE_CLASS_FIELD(NAME, TYPE) \
    static inline TYPE get_ ##NAME (Instance* self) { \
        return (TYPE)zre_field_get(self, #NAME); \
    } \
    static inline void set_ ##NAME (Instance* self, TYPE value) { \
        zre_field_set(self, #NAME, (uint64_t)value); \
    }

#define zre_call_type(obj, name, return_type, ...) \
    SUPPRESS_WARNINGS( \
        ((return_type (*)())zre_method_virtual(obj, name))(obj, ##__VA_ARGS__) \
    )

#define zre_call(obj, name, ...) zre_call_type(obj, name, Instance*, ##__VA_ARGS__)

// - String utilities
#define zstr(s) zre_string_literal(s)
#define zstr_get(s) ((const char*)zre_field_get(s, "cstr"))

// - Hashing utilities
uint64_t zre_hash(Instance* obj);
