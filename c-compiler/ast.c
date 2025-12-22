#include "ast.h"

#include <string.h>
#include <tree_sitter/api.h>

#define ts_node_valid(node) !(ts_node_is_null(node) || ts_node_is_error(node))
#define REQUIRE_NODE(node) if (!ts_node_valid(node)) return 0

#define static_strlen(s) (sizeof(s) / sizeof(s[0]) - 1)
#define ts_node_child_by_field(node, name) ts_node_child_by_field_name(node, name, static_strlen(name))

static const char* ts_node_content(TSNode node, const char* src, Arena* arena) {
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
                    TSNode returnTypeNode = ts_node_child_by_field(memberNode, "returnType");

                    members[j].type = CLASS_MEMBER_METHOD;
                    members[j].as.method = (MethodDecl){
                            .name = ts_node_content(nameNode, src, arena),
                            .returnType = ts_node_content(returnTypeNode, src, arena)
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