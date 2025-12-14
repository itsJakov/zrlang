#pragma once

#define DEFINE_FIELD(NAME, TYPE) \
    static inline TYPE get_ ##NAME (Instance* self) { \
        return (TYPE)zre_field_get(self, #NAME); \
    } \
    static inline void set_ ##NAME (Instance* self, TYPE value) { \
        zre_field_set(self, #NAME, (uint64_t)value); \
    }
