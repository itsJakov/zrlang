#pragma once

#include "arena.h"

#define Optional(T) T

#define NODE_HEADER uint16_t _type;

typedef union Expression Expression;

typedef struct {
    NODE_HEADER
    int64_t value;
} NumberExpr;

typedef struct {
    NODE_HEADER
    const char* value;
} StringExpr;

typedef struct {
    NODE_HEADER
    const char* value;
} Identifier;

typedef struct {
    NODE_HEADER
    Expression* expr;
    const char* memberName;
} MemberExpr;

typedef struct {
    NODE_HEADER
    Expression* callee;
    Expression* args;
} CallExpr;

typedef struct {
    NODE_HEADER
    const char* className;
} NewExpr;

union Expression {
    NODE_HEADER
    NumberExpr number;
    StringExpr string;
    Identifier identifier;
    MemberExpr member;
    CallExpr call;
    NewExpr newExpr;
};

typedef struct {
    NODE_HEADER
    Identifier name;
    Optional(Expression) value;
} VarStmt;

typedef union {
    NODE_HEADER
    VarStmt var;
    CallExpr call;
} Statement;

typedef struct {
    NODE_HEADER
    Identifier name;
    Optional(Identifier) returnType;
    Statement* block;
} MethodDecl;

typedef struct {
    NODE_HEADER
    Identifier name;
    Identifier type;
} ClassFieldDecl;

typedef union {
    NODE_HEADER
    ClassFieldDecl field;
    MethodDecl method;
} ClassMember;

typedef struct {
    NODE_HEADER
    Identifier name;
    Optional(Identifier) super;
    ClassMember* members;
} ClassDeclaration;

#define AST_NODES \
    X(member_expr, MemberExpr, expr, memberName) \
    X(call_expr, CallExpr, callee, args) \
    X(new_expr, NewExpr, className) \
    X(var_stmt, VarStmt, name, value) \
    X(method_decl, MethodDecl, name, returnType, block) \
    X(class_decl, ClassDeclaration, name, super, members) \
    X(class_field_decl, ClassFieldDecl, name, type)

#define AST_LISTS \
    X(source_file, ClassDeclaration) \
    X(call_args, Expression) \
    X(block, Statement) \
    X(class_members, ClassMember) \

#define X(node, Struct, ...) k ##Struct,
typedef enum {
    kNullNode = 0,
    kNumberExpr,
    kStringExpr,
    kIdentifierExpr,
    AST_NODES
} ASTNodeType;
#undef X

ClassDeclaration* buildAST(Arena* arena, const char* src, size_t srcLen);