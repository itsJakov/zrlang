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

    _expr: $ => choice(
        $.number_expr,
        $.string_expr,
        $.identifier,
        $.member_expr,
        $.call_expr,
        $.new_expr
    ),

    member_expr: $ => seq(
        field("expr", $._expr),
        ".",
        field("member", $.identifier)
    ),

    call_expr: $ => seq(
        field("callee", $._expr),
        "(",
        ")"
    ),

    new_expr: $ => seq(
        "new",
        field("className", $.identifier)
    ),

    var_stmt: $ => seq(
        "var",
        field("name", $.identifier),
        optional(seq("=", field("value", $._expr)))
    ),

    _stmt: $ => choice(
        $.var_stmt
    ),

    block: $ => seq("{", repeat($._stmt), "}"),

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
        /(\p{XID_Start}|\$|_|\\u[0-9A-Fa-f]{4}|\\U[0-9A-Fa-f]{8})(\p{XID_Continue}|\$|\\u[0-9A-Fa-f]{4}|\\U[0-9A-Fa-f]{8})*/,

    number_expr: _ => {
      const separator = '\'';
      const hex = /[0-9a-fA-F]/;
      const decimal = /[0-9]/;
      const hexDigits = seq(repeat1(hex), repeat(seq(separator, repeat1(hex))));
      const decimalDigits = seq(repeat1(decimal), repeat(seq(separator, repeat1(decimal))));
      return token(seq(
          optional(/[-\+]/),
          optional(choice(/0[xX]/, /0[bB]/)),
          choice(
              seq(
                  choice(
                      decimalDigits,
                      seq(/0[bB]/, decimalDigits),
                      seq(/0[xX]/, hexDigits),
                  ),
                  optional(seq('.', optional(hexDigits))),
              ),
              seq('.', decimalDigits),
          ),
          optional(seq(
              /[eEpP]/,
              optional(seq(
                  optional(/[-\+]/),
                  hexDigits,
              )),
          )),
          /[uUlLwWfFbBdD]*/,
      ));
    },

    string_expr: $ => seq(
        '"',
        repeat(choice(
            alias(token.immediate(prec(1, /[^\\"\n]+/)), $.string_content),
            $.escape_sequence,
        )),
        '"',
    ),

    escape_sequence: _ => token(prec(1, seq(
        '\\',
        choice(
            /[^xuU]/,
            /\d{2,3}/,
            /x[0-9a-fA-F]{1,4}/,
            /u[0-9a-fA-F]{4}/,
            /U[0-9a-fA-F]{8}/,
        ),
    ))),
  }
});
