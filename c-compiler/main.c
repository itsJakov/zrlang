#include <stdio.h>
#include <stddef.h>

#include <tree_sitter/api.h>
#include <string.h>

#define ARENA_IMPLEMENTATION
#include "arena.h"

#include "map.h"
#define FIELD(name, type) { #name, offsetof(type, name) }
#define STRUCT_META(type, ...) const FieldMeta type ##_meta[] = { MAP_LIST_UD(FIELD, type, __VA_ARGS__), {0} };

Arena arena = {0};

const TSLanguage* tree_sitter_zrlang(void);

static char* readFile(const char* filename, size_t* outSize) {
    FILE* file = fopen(filename, "r");
    if (!file) return NULL;

    fseek(file, 0, SEEK_END);
    size_t size = ftell(file);
    *outSize = size;
    fseek(file, 0, SEEK_SET);

    char* buffer = arena_alloc(&arena, size + 1);
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

typedef struct {
    StringView name;
    StringView super;
} ClassDeclaration;


#define TS_NODE_STRING_VIEW(node) ((StringView){ ts_node_start_byte(node), ts_node_end_byte(node) })

int main() {
    size_t sourceCodeSize;
    char* sourceCode = readFile("input.txt", &sourceCodeSize);

    TSParser *parser = ts_parser_new();

    ts_parser_set_language(parser, tree_sitter_zrlang());

    TSTree *tree = ts_parser_parse_string(parser, NULL, sourceCode, sourceCodeSize);

    TSNode rootNode = ts_tree_root_node(tree);
    for (size_t i = 0; i < ts_node_named_child_count(rootNode); i++) {
        TSNode classDef = ts_node_named_child(rootNode, i);

        TSNode className = ts_node_child_by_field_name(classDef, "name", 4);

        printStringView(sourceCode, &TS_NODE_STRING_VIEW(className));
    }

//    char *string = ts_node_string(rootNode);
//    printf("Syntax tree: %s\n", string);

    ts_tree_delete(tree);
    ts_parser_delete(parser);

    arena_free(&arena);
    return 0;
}