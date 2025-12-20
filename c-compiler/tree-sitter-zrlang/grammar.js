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
        field("returnType", optional(seq("->", $.identifier))),
        field("block", $.block)
    ),

    class_decl: $ => seq(
        "class",
        field("name", $.identifier),
        field("super", optional(seq(":", $.identifier))),
        "{",
        field("members", repeat($._class_member)),
        "}"
    ),

    _class_member: $ => choice(
        $.class_field_decl,
        $.method_decl
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
