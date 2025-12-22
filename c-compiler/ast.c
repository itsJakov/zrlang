#include "ast.h"

#include <string.h>
#include <tree_sitter/api.h>

#define ts_node_valid(node) !(ts_node_is_null(node) || ts_node_is_error(node))
#define REQUIRE_NODE(node) if (!ts_node_valid(node)) return 0

#define static_strlen(s) (sizeof(s) / sizeof(s[0]) - 1)
#define ts_node_child_by_field(node, name) ts_node_child_by_field_name(node, name, static_strlen(name))

static char* ts_node_content(TSNode node, const char* src, Arena* arena) {
    if (!ts_node_valid(node)) return NULL;
    size_t start = ts_node_start_byte(node);
    size_t end = ts_node_end_byte(node);

    size_t len = end - start;
    char* buffer = arena_alloc(arena, len+1);
    memcpy(buffer, src + start, len);
    buffer[len+1] = '\0';
    return buffer;
}

const TSLanguage* tree_sitter_zrlang(void);

// TODO: No TSNode error checking!
static Statement* buildBlock(TSNode node, const char* src, Arena* arena) {
    size_t count = ts_node_named_child_count(node);
    Statement* stmts = arena_alloc(arena, sizeof(Statement) * (count + 1));
    for (size_t i = 0; i < count; i++) {
        TSNode stmtNode = ts_node_named_child(node, i);
        if (strcmp(ts_node_type(stmtNode), "var_stmt") == 0) {
            TSNode nameNode = ts_node_child_by_field(stmtNode, "name");
            TSNode valueNode = ts_node_child_by_field(stmtNode, "value");

            Expression value;
            if (ts_node_is_null(valueNode)) {
                value = (Expression){0};
            } else if (strcmp(ts_node_type(valueNode), "number_expr") == 0) {
                value.type = EXPRESSION_NUMBER;
                Arena temp = {0};
                char* str = ts_node_content(valueNode, src, &temp);
                value.as.number = strtol(str, NULL, 0); // TODO: strtol could fail
                arena_free(&temp);
            } else if (strcmp(ts_node_type(valueNode), "string_expr") == 0) {
                value.type = EXPRESSION_STRING;
                char* str = ts_node_content(valueNode, src, arena);
                str += 1; // Move from the first "
                str[strlen(str) - 1] = '\0'; // Overwrite last " with a \0
                value.as.string = str;
            } else if (strcmp(ts_node_type(valueNode), "new_expr") == 0) {
                value.type = EXPRESSION_NEW;
                TSNode classNameNode = ts_node_child_by_field(valueNode, "className");
                value.as.newExpr = (NewExpr){
                    .className = ts_node_content(classNameNode, src, arena)
                };
            } else {
                abort();
            }

            stmts[i].type = STATEMENT_VAR;
            stmts[i].as.var = (VarStmt){
                .name = ts_node_content(nameNode, src, arena),
                .value = value
            };
        } else {
            abort();
        }
    }
    stmts[count] = (Statement){0};

    return stmts;
}

ClassDeclaration* buildAST(Arena* arena, const char* src, size_t srcLen) {
    TSParser *parser = ts_parser_new();
    ts_parser_set_language(parser, tree_sitter_zrlang());
    TSTree *tree = ts_parser_parse_string(parser, NULL, src, srcLen);

    TSNode rootNode = ts_tree_root_node(tree);
    size_t count = ts_node_named_child_count(rootNode);
    ClassDeclaration* classDeclarations = arena_alloc(arena, sizeof(ClassDeclaration) * (count + 1));
    for (size_t i = 0; i < count; i++) {
        TSNode classDef = ts_node_named_child(rootNode, i);
        REQUIRE_NODE(classDef);

        TSNode className = ts_node_child_by_field(classDef, "name");
        REQUIRE_NODE(className);

        TSNode superNode = ts_node_child_by_field(classDef, "super");

        TSNode membersNode = ts_node_child_by_field(classDef, "members");
        ClassMember* members;
        if (ts_node_valid(membersNode)) {
            size_t memberCount = ts_node_named_child_count(membersNode);
            members = arena_alloc(arena, sizeof(ClassMember) * (memberCount + 1));

            for (size_t j = 0; j < memberCount; j++) {
                TSNode memberNode = ts_node_named_child(membersNode, j);
                REQUIRE_NODE(memberNode);

                if (strcmp(ts_node_type(memberNode), "class_field_decl") == 0) {
                    TSNode nameNode = ts_node_child_by_field(memberNode, "name");
                    REQUIRE_NODE(nameNode);
                    TSNode typeNode = ts_node_child_by_field(memberNode, "type");
                    REQUIRE_NODE(typeNode);

                    members[j].type = CLASS_MEMBER_FIELD;
                    members[j].as.field = (ClassFieldDecl){
                            .name = ts_node_content(nameNode, src, arena),
                            .type = ts_node_content(typeNode, src, arena)
                    };
                } else if (strcmp(ts_node_type(memberNode), "method_decl") == 0) {
                    TSNode nameNode = ts_node_child_by_field(memberNode, "name");
                    REQUIRE_NODE(nameNode);
                    TSNode blockNode = ts_node_child_by_field(memberNode, "block");
                    REQUIRE_NODE(blockNode);

                    members[j].type = CLASS_MEMBER_METHOD;
                    members[j].as.method = (MethodDecl){
                            .name = ts_node_content(nameNode, src, arena),
                            .block = buildBlock(blockNode, src, arena)
                    };
                } else {
                    return false;
                }
            }

            members[memberCount] = (ClassMember){0};
        } else {
            members = arena_alloc(arena, sizeof(ClassMember));
            members[0] = (ClassMember){0};
        }

        classDeclarations[i] = (ClassDeclaration){
                .name = ts_node_content(className, src, arena),
                .super = ts_node_content(superNode, src, arena),
                .members = members
        };
    }
    classDeclarations[count] = (ClassDeclaration){0};

    ts_tree_delete(tree);
    ts_parser_delete(parser);

    return classDeclarations;
}