import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from lark import Lark, ast_utils, Transformer, Token

this_module = sys.modules[__name__]

class _Ast(ast_utils.Ast):
    pass

# Expressions
class _Expression(_Ast):
    pass

@dataclass
class IntExpr(_Expression):
    value: int

@dataclass
class LocalExpr(_Expression):
    local: str

@dataclass
class MemberExpr(_Expression):
    expr: _Expression
    member: str

@dataclass
class CallExpr(_Expression):
    callee: _Expression
    args: Optional[str] = None

@dataclass
class AllocExpr(_Expression):
    cls_name: str

# Statements
class _Statement(_Ast):
    pass

@dataclass
class VarStmt(_Statement):
    local: str
    expr: Optional[_Expression]

@dataclass
class CallStmt(_Statement):
    call: CallExpr

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
    super: str
    members: list[_ClassMember]

# Method / Function
@dataclass
class MethodDecl(_Ast):
    name: str
    block: list[_Statement]

class ToAst(Transformer):
    def block(self, l: list[_Statement]) -> list[_Statement]:
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

parser = Lark(Path("grammar.lark").read_text(), parser="lalr")
transformer = ast_utils.create_transformer(this_module, ToAst())

def parse(text):
    tree = parser.parse(text)
    return transformer.transform(tree)