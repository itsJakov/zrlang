#include <stdio.h>
#include <stddef.h>

#include <tree_sitter/api.h>
#include <string.h>

#define ARENA_IMPLEMENTATION
#include "arena.h"

#include "map.h"
#define FIELD(name, type) { #name, offsetof(type, name) }
#define STRUCT_META(type, ...) const FieldMeta type ##_meta[] = { MAP_LIST_UD(FIELD, type, __VA_ARGS__), {0} };

const TSLanguage* tree_sitter_zrlang(void);

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


typedef struct {
    size_t start;
    size_t end;
} StringView;

static void printStringView(const char* src, StringView* sv) {
    size_t len = sv->end - sv->start;
    char* buffer = malloc(len+1);
    memcpy(buffer, src + sv->start, len);
    buffer[len+1] = 0;
    puts(buffer);
    free(buffer);
}

static char* stringViewToCStr(Arena* arena, const char* src, StringView* sv) {
    size_t len = sv->end - sv->start;
    char* buffer = arena_alloc(arena, len+1);
    memcpy(buffer, src + sv->start, len);
    buffer[len+1] = 0;
    return buffer;
}

#define Optional(T) T

typedef struct {
    StringView name;
    Optional(StringView) returnType;
} MethodDecl;

typedef struct {
    StringView name;
    StringView type;
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
    StringView name;
    Optional(StringView) super;

    ClassMember* members;
} ClassDeclaration;


#define ts_node_string_view(node) ((StringView){ ts_node_start_byte(node), ts_node_end_byte(node) })

#define ts_node_valid(node) !(ts_node_is_null(node) || ts_node_is_error(node))
#define CHECK_NODE(node) if (!ts_node_valid(node)) return 0

#define static_strlen(s) (sizeof(s) / sizeof(s[0]) - 1)
#define ts_node_child_by_field(node, name) ts_node_child_by_field_name(node, name, static_strlen(name))

ClassDeclaration* buildAST(Arena* arena, const char* src, size_t srcLen) {
    TSParser *parser = ts_parser_new();
    ts_parser_set_language(parser, tree_sitter_zrlang());
    TSTree *tree = ts_parser_parse_string(parser, NULL, src, srcLen);

    TSNode rootNode = ts_tree_root_node(tree);
    size_t count = ts_node_named_child_count(rootNode);
    ClassDeclaration* classDeclarations = arena_alloc(arena, sizeof(ClassDeclaration) * (count + 1));
    for (size_t i = 0; i < count; i++) {
        TSNode classDef = ts_node_named_child(rootNode, i);
        CHECK_NODE(classDef);

        TSNode className = ts_node_child_by_field(classDef, "name");
        CHECK_NODE(className);

        TSNode superNode = ts_node_child_by_field(classDef, "super");
        StringView super = {0};
        if (ts_node_valid(superNode)) {
            super = ts_node_string_view(superNode);
        }

        TSNode membersNode = ts_node_child_by_field(classDef, "members");
        ClassMember* members;
        if (ts_node_valid(membersNode)) {
            size_t memberCount = ts_node_named_child_count(membersNode);
            members = arena_alloc(arena, sizeof(ClassMember) * (memberCount + 1));

            for (size_t j = 0; j < memberCount; j++) {
                TSNode memberNode = ts_node_named_child(membersNode, j);
                CHECK_NODE(memberNode);

                if (strcmp(ts_node_type(memberNode), "class_field_decl") == 0) {
                    TSNode nameNode = ts_node_child_by_field(memberNode, "name");
                    CHECK_NODE(nameNode);
                    TSNode typeNode = ts_node_child_by_field(memberNode, "type");
                    CHECK_NODE(typeNode);

                    members[j].type = CLASS_MEMBER_FIELD;
                    members[j].as.field = (ClassFieldDecl){
                        .name = ts_node_string_view(nameNode),
                        .type = ts_node_string_view(typeNode)
                    };
                } else if (strcmp(ts_node_type(memberNode), "method_decl") == 0) {
                    TSNode nameNode = ts_node_child_by_field(memberNode, "name");
                    CHECK_NODE(nameNode);
                    TSNode returnTypeNode = ts_node_child_by_field(memberNode, "returnType");

                    members[j].type = CLASS_MEMBER_METHOD;
                    members[j].as.method = (MethodDecl){
                        .name = ts_node_string_view(nameNode),
                        .returnType = ts_node_valid(returnTypeNode) ? ts_node_string_view(returnTypeNode) : (StringView){0}
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
                .name = ts_node_string_view(className),
                .super = super,
                .members = members
        };
    }
    classDeclarations[count] = (ClassDeclaration){0};

    ts_tree_delete(tree);
    ts_parser_delete(parser);

    return classDeclarations;
}



int main() {
    Arena arena = {0};

    size_t sourceCodeLen;
    char* sourceCode = readFile(&arena, "input.txt", &sourceCodeLen);

    ClassDeclaration* ast = buildAST(&arena, sourceCode, sourceCodeLen);

    for (ClassDeclaration* cls = ast; cls->name.start != 0; cls++) {
        printf("Class %s, super: %s {\n",
               stringViewToCStr(&arena, sourceCode, &cls->name),
               stringViewToCStr(&arena, sourceCode, &cls->super));

        for (ClassMember* member = cls->members; member->type != 0; member++) {
            printf("\tMember: ");
            switch (member->type) {
                case CLASS_MEMBER_FIELD: {
                    ClassFieldDecl* field = &member->as.field;
                    printf("Field: name = %s, type = %s\n",
                           stringViewToCStr(&arena, sourceCode, &field->name),
                           stringViewToCStr(&arena, sourceCode, &field->type));
                    break;
                }
                case CLASS_MEMBER_METHOD: {
                    MethodDecl* method = &member->as.method;
                    printf("Method: name = %s, returnType = %s\n",
                           stringViewToCStr(&arena, sourceCode, &method->name),
                           stringViewToCStr(&arena, sourceCode, &method->returnType));
                    break;
                }
            }
        }

        printf("}\n");
    }

    arena_free(&arena);
    return 0;
}