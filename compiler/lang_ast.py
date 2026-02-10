import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from lark import Lark, ast_utils, Transformer, Token
from lark.tree import Meta

this_module = sys.modules[__name__]

@dataclass
class _Ast(ast_utils.Ast, ast_utils.WithMeta):
    meta: Meta

# Expressions
class _Expression(_Ast):
    pass

@dataclass
class IntExpr(_Expression):
    value: int

@dataclass
class StringExpr(_Expression):
    value: str

@dataclass
class SymbolExpr(_Expression):
    name: str

@dataclass
class MemberExpr(_Expression):
    expr: _Expression
    member: str

@dataclass
class CallExpr(_Expression):
    callee: _Expression
    args: list[_Expression]

@dataclass
class AllocExpr(_Expression):
    cls_name: str

class BinaryOperation(Enum):
    # Comparison
    EQ = "=="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    # Arithmetic
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    # Logical
    AND = "&&"
    OR = "||"

@dataclass
class BinaryExpr(_Expression):
    lhs: _Expression
    op: BinaryOperation
    rhs: _Expression

    def __init__(self, meta: Meta, lhs: _Expression, op: Token, rhs: _Expression):
        super().__init__(meta)
        self.lhs = lhs
        self.op = BinaryOperation(op.value)
        self.rhs = rhs

class UnaryOperation(Enum):
    NOT = "!"
    NEG = "-"
    POS = "+"

@dataclass
class UnaryExpr(_Expression):
    op: UnaryOperation
    expr: _Expression

# Statements
class _Statement(_Ast):
    pass

@dataclass
class VarStmt(_Statement):
    local: str
    expr: Optional[_Expression]

@dataclass
class ExprStmt(_Statement):
    expr: _Expression

@dataclass
class AssignStmt(_Statement):
    assignee: _Expression
    value: _Expression

@dataclass
class IfStmt(_Statement):
    condition: _Expression
    block: list[_Statement]
    else_block: Optional[list[_Statement]]

# Class
class _ClassMember(_Ast):
    pass

@dataclass
class ClassField(_ClassMember):
    name: str
    type: str

@dataclass
class ClassDecl(_Ast):
    name: str
    super: Optional[str]
    members: list[_ClassMember]

# Method / Function
@dataclass
class MethodDecl(_Ast):
    name: str
    block: list[_Statement]

class ToAst(Transformer):
    def block(self, l: list[_Statement]) -> list[_Statement]:
        return l

    def call_args(self, l: list[_Expression]) -> list[_Expression]:
        if l[0] is None: return [] # Lark behaviour I don't feel like thinking about
        return l

    def class_body(self, l: list[_ClassMember]) -> list[_ClassMember]:
        return l

    def SIGNED_NUMBER(self, t: Token) -> int:
        return int(t.value)

    def ESCAPED_STRING(self, t: Token) -> str:
        return t[1:-1] # Remove quotation marks

    def CNAME(self, t: Token) -> str:
        return t.value

    def start(self, class_decls: list[ClassDecl]):
        return class_decls

parser = Lark(Path("grammar.lark").read_text(), parser="lalr", propagate_positions=True)
transformer = ast_utils.create_transformer(this_module, ToAst())

def parse(text):
    tree = parser.parse(text)
    return transformer.transform(tree)