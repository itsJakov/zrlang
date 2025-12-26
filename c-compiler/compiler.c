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
    switch (expr->_type) {
        case kNumberExpr: {
            return arena_sprintf(arena, "%lld", expr->number);
        }
        case kIdentifierExpr: {
            return arena_sprintf(arena, "%%%s", expr->identifier);
        }
        case kStringExpr: {
            char* temp = getLocal(f, arena, local);
            fprintf(f, "\t%s =l add $strings, %lu\n", temp, offsetForString(expr->string.value));
            return temp;
        }
        case kMemberExpr: {
            MemberExpr* member = &expr->member;
            char* sym = exprIntoLocal(f, member->expr, NULL, arena);
            char* temp = getLocal(f, arena, local);

            fprintf(f, "\t%%_str =l add $strings, %lu\n", offsetForString(member->memberName));
            fprintf(f, "\t%s =l call $zre_get_field(l %s, l %%_str)\n", temp, sym);
            return temp;
        }
        case kCallExpr: {
            CallExpr* call = &expr->call;
            Expression* callee = call->callee;

            char* argsStr = NULL;
            for (Expression* arg = call->args; arg->_type != kNullNode; arg++) {
                arrput(argsStr, 'l');
                arrput(argsStr, ' ');
                char* sym = exprIntoLocal(f, arg, NULL, arena);
                size_t len = strlen(sym);
                memcpy(arraddnptr(argsStr, len), sym, len);
                arrput(argsStr, ',');
                arrput(argsStr, ' ');
            }
            arrput(argsStr, '\0');

            char* temp;
            switch (callee->_type) {
                case kIdentifierExpr: {
                    temp = getLocal(f, arena, local);
                    fprintf(f, "\t%s =l call $__zre_%s(%s)\n", temp, callee->identifier.value, argsStr);
                    break;
                }
                case kMemberExpr: {
                    char* calleeTemp = exprIntoLocal(f, callee->member.expr, NULL, arena);

                    fprintf(f, "\t%%_str =l add $strings, %lu\n", offsetForString(callee->member.memberName));
                    fprintf(f, "\t%%_fn =l call $zre_method_virtual(l %s, l %%_str)\n", calleeTemp);
                    temp = getLocal(f, arena, local);
                    fprintf(f, "\t%s =l call %%_fn(l %s, %s)\n", temp, calleeTemp, argsStr);
                    break;
                }
                default:
                    fprintf(stderr, "Semantic error: Not a callable statement!\n");
                    abort();
            }

            arrfree(argsStr);
            return temp;
        }
        case kNewExpr: {
            char* temp = getLocal(f, arena, local);
            fprintf(f, "\t%s =l call $zre_alloc(l $%s)\n", temp, expr->newExpr.className);
            return temp;
        }
        default: abort_bug("Unknown expr type");
    }
}

static void compileBlock(FILE* f, Statement* block) {
    for (Statement* stmt = block; stmt->_type != kNullNode; stmt++) {
        switch (stmt->_type) {
            case kVarStmt: {
                VarStmt* var = &stmt->var;
                Expression* expr = &var->value;
                if (expr->_type == kNullNode) {
                    fprintf(f, "\t%%%s =l copy 0\n", var->name.value);
                    break;
                }

                switch (expr->_type) {
                    case kNumberExpr: {
                        fprintf(f, "\t%%%s =l copy %lld\n", var->name.value, expr->number.value);
                        break;
                    }
                    case kStringExpr: {
                        fprintf(f, "\t%%%s =l add $strings, %lu\n", var->name.value,
                                offsetForString(expr->string.value));
                        break;
                    }
                    default: {
                        Arena scratch = {0};
                        exprIntoLocal(f, expr, var->name.value, &scratch);
                        arena_free(&scratch);
                    }
                }

                break;
            }
            case kCallExpr: {
                Arena scratch = {0};
                exprIntoLocal(f, &(Expression){ .call = stmt->call }, NULL, &scratch);
                arena_free(&scratch);
                break;
            }
            default: abort_bug("Unknown statement type!\n");
        }
    }
}

static void compileInstanceMethod(FILE* f, ClassDeclaration* cls, MethodDecl* method) {
    fprintf(f, "function l $%s_%s(l %%self) {\n", cls->name.value, method->name.value);
    fprintf(f, "@start\n");
    compileBlock(f, method->block);
    fprintf(f, "\tret\n");
    fprintf(f, "}\n\n");
}

static void compileClass(FILE* f, ClassDeclaration* cls) {
    fprintf(f, "# ==== \"%s\" Class Definition ====\n", cls->name.value);

    fprintf(f, "data $%s_fields = {\n", cls->name.value);
    size_t fieldCount = 0;
    for (ClassMember* member = cls->members; member->_type != kNullNode; member++) {
        if (member->_type != kClassFieldDecl) continue;
        ClassFieldDecl* field = &member->field;
        fprintf(f, "\tl %s, l 0,\n", stringSymbol(field->name.value));
        fieldCount++;
    }
    fprintf(f, "}\n");

    fprintf(f, "data $%s_instanceMethods = {\n", cls->name.value);
    size_t instanceMethodCount = 0;
    for (ClassMember* member = cls->members; member->_type != kNullNode; member++) {
        if (member->_type != kMethodDecl) continue;
        MethodDecl* method = &member->method;
        fprintf(f, "\tl %s, l $%s_%s,\n", stringSymbol(method->name.value), cls->name.value, method->name.value);
        instanceMethodCount++;
    }
    fprintf(f, "}\n");

    fprintf(f, "export data $%s = {\n", cls->name.value);
    fprintf(f, "\tl %s,\n", stringSymbol(cls->name.value));
    if (cls->super.value == NULL)
        fprintf(f, "\tl 0,\n");
    else
        fprintf(f, "\tl %s,\n", cls->super.value);
    fprintf(f, "\tl %lu, l $%s_fields,\n", fieldCount, cls->name.value);
    fprintf(f, "\tl 0, l 0,\n");
    fprintf(f, "\tl %lu, l $%s_instanceMethods,\n", instanceMethodCount, cls->name.value);
    fprintf(f, "}\n\n");

    for (ClassMember* member = cls->members; member->_type != kNullNode; member++) {
        if (member->_type != kMethodDecl) continue;
        compileInstanceMethod(f, cls, &member->method);
    }

    fprintf(f, "\n");
}

void compile(const char* src, ClassDeclaration* classDecls) {
    FILE* f = fopen("ir.ssa", "w");

    fprintf(f, "# ==== Generated by zrc ==== \n\n");

    for (ClassDeclaration* cls = classDecls; cls->_type != kNullNode; cls++) {
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