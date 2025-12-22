#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

#include "ast.h"
#include "compiler.h"

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

int main() {
    Arena astArena = {0};

    size_t sourceCodeLen;
    char* sourceCode = readFile(&astArena, "input.txt", &sourceCodeLen);

    ClassDeclaration* ast = buildAST(&astArena, sourceCode, sourceCodeLen);

    for (ClassDeclaration* cls = ast; cls->name != NULL; cls++) {
        printf("Class %s, super: %s {\n", cls->name, cls->super);

        for (ClassMember* member = cls->members; member->type != 0; member++) {
            printf("\tMember: ");
            switch (member->type) {
                case CLASS_MEMBER_FIELD: {
                    ClassFieldDecl* field = &member->as.field;
                    printf("Field: name = %s, type = %s\n", field->name, field->type);
                    break;
                }
                case CLASS_MEMBER_METHOD: {
                    MethodDecl* method = &member->as.method;
                    printf("Method: name = %s, returnType = %s\n", method->name, method->returnType);
                    break;
                }
            }
        }

        printf("}\n");
    }

    compile(sourceCode, ast);

    arena_free(&astArena);
    return 0;
}