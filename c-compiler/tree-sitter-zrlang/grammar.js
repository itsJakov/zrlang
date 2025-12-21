/**
 * @file Zrlang grammar for tree-sitter
 * @author itsJakov
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

export default grammar({
  name: "zrlang",

  rules: {
    source_file: $ => repeat($.class_decl),

    block: $ => seq("{", "}"),

    method_decl: $ => seq(
        "func",
        field("name", $.identifier),
        "(",
        ")",
        optional(seq("->", field("returnType", $.identifier))),
        field("block", $.block)
    ),

    class_decl: $ => seq(
        "class",
        field("name", $.identifier),
        optional(seq(":", field("super", $.identifier))),
        field("members", $.class_members),
    ),

    class_members: $ => seq(
        "{",
        repeat(choice(
            $.class_field_decl,
            $.method_decl
        )),
        "}"
    ),

    class_field_decl: $ => seq(
        "var",
        field("name", $.identifier),
        ":",
        field("type", $.identifier)
    ),

    identifier: _ =>
        /(\p{XID_Start}|\$|_|\\u[0-9A-Fa-f]{4}|\\U[0-9A-Fa-f]{8})(\p{XID_Continue}|\$|\\u[0-9A-Fa-f]{4}|\\U[0-9A-Fa-f]{8})*/
  }
});
