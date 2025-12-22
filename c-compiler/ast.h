#pragma once

#include "arena.h"

#define Optional(T) T

typedef struct {
    const char* name;
    Optional(const char*) returnType;
} MethodDecl;

typedef struct {
    const char* name;
    const char* type;
} ClassFieldDecl;

typedef struct {
    enum {
        CLASS_MEMBER_FIELD = 1,
        CLASS_MEMBER_METHOD
    } type;
    union {
        ClassFieldDecl field;
        MethodDecl method;
    } as;
} ClassMember;

typedef struct {
    const char* name;
    Optional(const char*) super;

    ClassMember* members;
} ClassDeclaration;

ClassDeclaration* buildAST(Arena* arena, const char* src, size_t srcLen);