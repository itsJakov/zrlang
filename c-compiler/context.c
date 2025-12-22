#include "context.h"

#define STB_DS_IMPLEMENTATION
#include "../runtime/lib/stb_ds.h"

UnitContext UnitContext_current = {0};

struct StringMap { char* key; size_t value; };

size_t offsetForString(const char* str) {
    UnitContext* ctx = &UnitContext_current;

    StringMap* entry = shgetp_null(ctx->stringOffsets, str);
    if (entry != NULL) return entry->value;

    size_t offset = ctx->currentStringOffset;
    arrput(ctx->strings, str);
    shput(ctx->stringOffsets, str, offset);

    ctx->currentStringOffset += strlen(str) + 1;

    return offset;
}

const char* stringSymbol(const char* str) {
    static char buffer[1024]; // TODO: make this dynamic
    size_t offset = offsetForString(str);
    snprintf(buffer, 1024, "$strings+%lu", offset);
    return buffer;
}