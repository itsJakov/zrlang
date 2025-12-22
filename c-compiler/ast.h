#pragma once

#include "arena.h"

#define Optional(T) T

typedef struct {
    enum {
        EXPRESSION_NUMBER = 1,
        EXPRESSION_STRING
    } type;
    union {
        int64_t number;
        const char* string;
    } as;
} Expression;

typedef struct {
    const char* name;
    Optional(Expression) value;
} VarStmt;

typedef struct {
    enum {
        STATEMENT_VAR = 1,
    } type;
    union {
        VarStmt var;
    } as;
} Statement;

typedef struct {
    const char* name;
    Statement* block;
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