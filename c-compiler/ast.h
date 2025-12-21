#pragma once

#include "string-slice.h"
#include "arena.h"

#define Optional(T) T

typedef struct {
    StringSlice name;
    Optional(StringSlice) returnType;
} MethodDecl;

typedef struct {
    StringSlice name;
    StringSlice type;
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
    StringSlice name;
    Optional(StringSlice) super;

    ClassMember* members;
} ClassDeclaration;

ClassDeclaration* buildAST(Arena* arena, const char* src, size_t srcLen);