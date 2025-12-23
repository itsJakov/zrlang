#pragma once

#include "arena.h"

#define Optional(T) T

typedef struct Expression Expression;

typedef struct {
    Expression* expr;
    const char* memberName;
} MemberExpr;

typedef struct {
    Expression* callee;
    Expression* args;
} CallExpr;

typedef struct {
    const char* className;
} NewExpr;

struct Expression {
    enum {
        EXPRESSION_NUMBER = 1,
        EXPRESSION_STRING,
        EXPRESSION_IDENTIFIER,
        EXPRESSION_MEMBER,
        EXPRESSION_CALL,
        EXPRESSION_NEW
    } type;
    union {
        int64_t number;
        const char* string;
        const char* identifier;
        MemberExpr member;
        CallExpr call;
        NewExpr newExpr;
    } as;
};

typedef struct {
    const char* name;
    Optional(Expression) value;
} VarStmt;

typedef struct {
    Expression callExpr;
} CallStmt;

typedef struct {
    enum {
        STATEMENT_VAR = 1,
        STATEMENT_CALL
    } type;
    union {
        VarStmt var;
        CallStmt call;
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