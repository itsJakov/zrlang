#include "ast.h"

#include <string.h>
#include <tree_sitter/api.h>

#include "map.h"

#define BUILDER_FN(_node, Type) static bool _node ##__builder(TSNode node, Type* out, const char* src, Arena* arena)
typedef bool (*Builder)(TSNode node, void* out, const char* src, Arena* arena);
static bool buildNode(TSNode node, void* out, const char* src, Arena* arena);

#define ts_node_valid(node) !(ts_node_is_null(node) || ts_node_is_error(node))

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

#define static_strlen(s) (sizeof(s) / sizeof(s[0]) - 1)

#define Y(name) buildNode(ts_node_child_by_field_name(node, #name, static_strlen(#name)), &out->name, src, arena);
#define X(_node, Struct, ...) \
    BUILDER_FN(_node, Struct) { \
        *out = (Struct){0}; \
        out->_type = k ##Struct; \
        MAP(Y, __VA_ARGS__) \
        return true; \
    }
AST_NODES
#undef Y
#undef X

#define X(_node, Item) \
    BUILDER_FN(_node, Item*) { \
        size_t count = ts_node_named_child_count(node); \
        Item* list = arena_alloc(arena, sizeof(Item) * (count+1)); \
        list[count] = (Item){0}; \
        for (size_t i = 0; i < count; i++) \
            buildNode(ts_node_named_child(node, i), list + i, src, arena); \
        *out = list; \
        return true; \
    }
AST_LISTS
#undef X

typedef struct {
    const char* node;
    Builder fn;
} BuilderEntry;

#define REGISTER(_node, ...) { #_node, (Builder)_node ##__builder },
#define BUILDER_ENTRIES(...) MAP(REGISTER, __VA_ARGS__)

BUILDER_FN(number_expr, NumberExpr) {
    Arena temp = {0};
    char* str = ts_node_content(node, src, &temp);
    *out = (NumberExpr){
        ._type = kNumberExpr,
        .value = strtol(str, NULL, 0) // TODO: strtol could fail
    };
    arena_free(&temp);
    return true;
}

BUILDER_FN(string_expr, StringExpr) {
    char* str = ts_node_content(node, src, arena);
    str += 1; // Move from the first "
    str[strlen(str) - 1] = '\0'; // Overwrite last " with a \0
    *out = (StringExpr){
        ._type = kStringExpr,
        .value = str
    };
    return true;
}

BUILDER_FN(identifier, Identifier) {
    *out = (Identifier){
        ._type = kIdentifierExpr,
        .value = ts_node_content(node, src, arena)
    };
    return true;
}

const BuilderEntry builders[] = {
#define X REGISTER
        AST_NODES
        AST_LISTS
#undef X
        BUILDER_ENTRIES(number_expr, string_expr, identifier)
};

static bool buildNode(TSNode node, void* out, const char* src, Arena* arena) {
    if (!ts_node_valid(node)) {
        printf("Invalid node!");
        if (!ts_node_is_null(node) && ts_node_has_error(node)) {
            printf("not null but has errors");
        }
        printf("\n");
        return true;
    }

    const char* nodeType = ts_node_type(node);
    static size_t count = sizeof(builders) / sizeof(BuilderEntry);
    for (size_t i = 0; i < count; i++) {
        if (strcmp(builders[i].node, nodeType) == 0) {
            return builders[i].fn(node, out, src, arena);
        }
    }
    fprintf(stderr, "[BUG] No builder for node %s!\n", nodeType);
    *(char*)out = 0;
    return false;
//    abort();
}

const TSLanguage* tree_sitter_zrlang(void);

ClassDeclaration* buildAST(Arena* arena, const char* src, size_t srcLen) {
    TSParser *parser = ts_parser_new();
    ts_parser_set_language(parser, tree_sitter_zrlang());
    TSTree *tree = ts_parser_parse_string(parser, NULL, src, srcLen);

    TSNode rootNode = ts_tree_root_node(tree);

    ClassDeclaration* classes;
    source_file__builder(rootNode, &classes, src, arena);

    ts_tree_delete(tree);
    ts_parser_delete(parser);

    return classes;
}