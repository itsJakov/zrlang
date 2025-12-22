#include "compiler.h"

#include "context.h"

#define abort_bug(format, ...) fprintf(stderr, "[Bug] " format "\n", ##__VA_ARGS__); abort()

static char* getLocal(FILE* f, Arena* arena, Optional(const char*) name) {
    if (name != NULL) return arena_sprintf(arena, "%%%s", name);

    FunctionContext* ctx = &FunctionContext_current;
    char* local = arena_sprintf(arena, "%%_local%lu", ctx->temporaryIndex);
    ctx->temporaryIndex++;
    return local;
}

static char* exprIntoLocal(FILE* f, Expression* expr, Optional(const char*) local, Arena* arena) {
    switch (expr->type) {
        case EXPRESSION_NUMBER: {
            return arena_sprintf(arena, "%lld", expr->as.number);
        }
        case EXPRESSION_IDENTIFIER: {
            return arena_sprintf(arena, "%%%s", expr->as.identifier);
        }
        case EXPRESSION_STRING: {
            char* temp = getLocal(f, arena, local);
            fprintf(f, "\t%s =l add $strings, %lu\n", temp, offsetForString(expr->as.string));
            return temp;
        }
        case EXPRESSION_MEMBER: {
            MemberExpr* member = &expr->as.member;
            char* sym = exprIntoLocal(f, member->expr, NULL, arena);
            char* temp = getLocal(f, arena, local);

            fprintf(f, "\t%%_str =l add $strings, %lu\n", offsetForString(member->memberName));
            fprintf(f, "\t%s =l call $zre_get_field(l %s, l %%_str)\n", temp, sym);
            return temp;
        }
        case EXPRESSION_NEW: {
            char* temp = getLocal(f, arena, local);
            fprintf(f, "\t%s =l call $zre_alloc(l $%s)\n", temp, expr->as.newExpr.className);
            return temp;
        }
        default: abort_bug("Unknown expr type");
    }
}

static void compileBlock(FILE* f, Statement* block) {
    for (Statement* stmt = block; stmt->type != 0; stmt++) {
        switch (stmt->type) {
            case STATEMENT_VAR: {
                VarStmt* var = &stmt->as.var;
                Expression* expr = &var->value;
                if (expr->type == 0) {
                    fprintf(f, "\t%%%s =l copy 0\n", stmt->as.var.name);
                    break;
                }

                switch (expr->type) {
                    case EXPRESSION_NUMBER: {
                        fprintf(f, "\t%%%s =l copy %lld\n", stmt->as.var.name, expr->as.number);
                        break;
                    }
                    case EXPRESSION_STRING: {
                        fprintf(f, "\t%%%s =l add $strings, %lu\n", stmt->as.var.name,
                                offsetForString(expr->as.string));
                        break;
                    }
                    default: {
                        Arena scratch = {0};
                        exprIntoLocal(f, expr, var->name, &scratch); // resolve expr as a temporary
                        arena_free(&scratch);
                    }
                }

                break;
            }
            default: abort_bug("Unknown statement type!\n");
        }
    }
}

static void compileInstanceMethod(FILE* f, ClassDeclaration* cls, MethodDecl* method) {
    fprintf(f, "function l $%s_%s(l %%self) {\n", cls->name, method->name);
    fprintf(f, "@start\n");
    compileBlock(f, method->block);
    fprintf(f, "\tret\n");
    fprintf(f, "}\n\n");
}

static void compileClass(FILE* f, ClassDeclaration* cls) {
    fprintf(f, "# ==== \"%s\" Class Definition ====\n", cls->name);

    fprintf(f, "data $%s_fields = {\n", cls->name);
    size_t fieldCount = 0;
    for (ClassMember* member = cls->members; member->type != 0; member++) {
        if (member->type != CLASS_MEMBER_FIELD) continue;
        ClassFieldDecl* field = &member->as.field;
        fprintf(f, "\tl %s, l 0,\n", stringSymbol(field->name));
        fieldCount++;
    }
    fprintf(f, "}\n");

    fprintf(f, "data $%s_instanceMethods = {\n", cls->name);
    size_t instanceMethodCount = 0;
    for (ClassMember* member = cls->members; member->type != 0; member++) {
        if (member->type != CLASS_MEMBER_METHOD) continue;
        MethodDecl* method = &member->as.method;
        fprintf(f, "\tl %s, l $%s_%s,\n", stringSymbol(method->name), cls->name, method->name);
        instanceMethodCount++;
    }
    fprintf(f, "}\n");

    fprintf(f, "export data $%s = {\n", cls->name);
    fprintf(f, "\tl %s,\n", stringSymbol(cls->name));
    if (cls->super == NULL)
        fprintf(f, "\tl 0,\n");
    else
        fprintf(f, "\tl %s,\n", cls->super);
    fprintf(f, "\tl %lu, l $%s_fields,\n", fieldCount, cls->name);
    fprintf(f, "\tl 0, l 0,\n");
    fprintf(f, "\tl %lu, l $%s_instanceMethods,\n", instanceMethodCount, cls->name);
    fprintf(f, "}\n\n");

    for (ClassMember* member = cls->members; member->type != 0; member++) {
        if (member->type != CLASS_MEMBER_METHOD) continue;
        compileInstanceMethod(f, cls, &member->as.method);
    }

    fprintf(f, "\n");
}

void compile(const char* src, ClassDeclaration* classDecls) {
    FILE* f = fopen("ir.ssa", "w");

    fprintf(f, "# ==== Generated by zrc ==== \n\n");

    for (ClassDeclaration* cls = classDecls; cls->name != NULL; cls++) {
        compileClass(f, cls);
    }

    UnitContext* ctx = &UnitContext_current;
    fprintf(f, "# ==== String Data ==== \n");
    fprintf(f, "data $strings = { b \"");
    for (size_t i = 0; i < arrlen(ctx->strings); i++) {
        fprintf(f, "%s\\0", ctx->strings[i]);
    }
    fprintf(f, "\" }\n");

    fclose(f);
}