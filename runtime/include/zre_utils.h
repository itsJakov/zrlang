#pragma once

#define DEFINE_FIELD(NAME, TYPE) \
    static inline TYPE get_ ##NAME (Instance* self) { \
        return (TYPE)zre_field_get(self, #NAME); \
    } \
    static inline void set_ ##NAME (Instance* self, TYPE value) { \
        zre_field_set(self, #NAME, (uint64_t)value); \
    }

#define SUPPRESS_WARNINGS(code) \
    _Pragma("GCC diagnostic push") \
    _Pragma("GCC diagnostic ignored \"-Wdeprecated-non-prototype\"") \
    code \
    _Pragma("GCC diagnostic pop")

#define zre_call(obj, name, ...) \
    SUPPRESS_WARNINGS( \
        ((Instance* (*)())zre_method_virtual(obj, name))(obj, ##__VA_ARGS__) \
    )

#define zstr_buf(s) ((const char*)zre_field_get(s, "cstr"))