#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

#include "ast.h"

#define ARENA_IMPLEMENTATION
#include "arena.h"

static char* readFile(Arena* arena, const char* filename, size_t* outLen) {
    FILE* file = fopen(filename, "r");
    if (!file) return NULL;

    fseek(file, 0, SEEK_END);
    size_t size = ftell(file);
    *outLen = size;
    fseek(file, 0, SEEK_SET);

    char* buffer = arena_alloc(arena, size + 1);
    if (!buffer) {
        fclose(file);
        return NULL;
    }

    fread(buffer, 1, size, file);
    buffer[size] = '\0';

    fclose(file);
    return buffer;
}

static void printSlice(const char* src, StringSlice* slice) {
    if (stringSliceIsNull(slice)) puts("<NULL>");

    size_t len = slice->end - slice->start;
    char* buffer = malloc(len+1);
    memcpy(buffer, src + slice->start, len);
    buffer[len+1] = 0;
    puts(buffer);
    free(buffer);
}

static char* sliceToCStr(Arena* arena, const char* src, StringSlice* slice) {
    if (stringSliceIsNull(slice)) return "<NULL>";

    size_t len = slice->end - slice->start;
    char* buffer = arena_alloc(arena, len+1);
    memcpy(buffer, src + slice->start, len);
    buffer[len+1] = 0;
    return buffer;
}


int main() {
    Arena arena = {0};

    size_t sourceCodeLen;
    char* sourceCode = readFile(&arena, "input.txt", &sourceCodeLen);

    ClassDeclaration* ast = buildAST(&arena, sourceCode, sourceCodeLen);

    for (ClassDeclaration* cls = ast; cls->name.start != 0; cls++) {
        printf("Class %s, super: %s {\n",
               sliceToCStr(&arena, sourceCode, &cls->name),
               sliceToCStr(&arena, sourceCode, &cls->super));

        for (ClassMember* member = cls->members; member->type != 0; member++) {
            printf("\tMember: ");
            switch (member->type) {
                case CLASS_MEMBER_FIELD: {
                    ClassFieldDecl* field = &member->as.field;
                    printf("Field: name = %s, type = %s\n",
                           sliceToCStr(&arena, sourceCode, &field->name),
                           sliceToCStr(&arena, sourceCode, &field->type));
                    break;
                }
                case CLASS_MEMBER_METHOD: {
                    MethodDecl* method = &member->as.method;
                    printf("Method: name = %s, returnType = %s\n",
                           sliceToCStr(&arena, sourceCode, &method->name),
                           sliceToCStr(&arena, sourceCode, &method->returnType));
                    break;
                }
            }
        }

        printf("}\n");
    }

    arena_free(&arena);
    return 0;
}