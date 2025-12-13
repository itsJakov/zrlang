import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from lark import Lark, ast_utils, Transformer, Token

this_module = sys.modules[__name__]

class _Ast(ast_utils.Ast):
    pass

@dataclass
class FullName(_Ast, ast_utils.AsList):
    parts: List[str]

class _Expression(_Ast):
    pass

@dataclass
class IntExpr(_Expression):
    value: int

@dataclass
class StringExpr(_Expression):
    value: str

@dataclass
class LocalExpr(_Expression):
    local_name: str

@dataclass
class CallArgs(_Ast, ast_utils.AsList):
    exprs: List[_Expression]

@dataclass
class CallExpr(_Expression):
    full_name: FullName
    args: CallArgs

class _Statement(_Ast):
    pass

@dataclass
class Block(_Ast, ast_utils.AsList):
    stmts: List[_Statement]

@dataclass
class VarStmt(_Statement):
    local_name: str
    expr: _Expression

@dataclass
class CallStmt(_Statement):
    expr: CallExpr

@dataclass
class PrintStmt(_Statement):
    expr: _Expression

@dataclass
class IfStmt(_Statement):
    expr: _Expression
    block: Block

    elseIfExpr: Optional[_Expression]
    elseIfBlock: Optional[Block]

    elseBlock: Optional[Block]

@dataclass
class MethodDecl(_Ast):
    name: str
    return_type: str
    block: Block

class ToAst(Transformer):
    def SIGNED_NUMBER(self, t: Token) -> int:
        return int(t.value)

    def ESCAPED_STRING(self, t: Token) -> str:
        return t[1:-1] # Remove quotation marks

    def CNAME(self, t: Token) -> str:
        return t.value

    def start(self, method_decls: List[MethodDecl]):
        return method_decls

parser = Lark(Path("grammar.lark").read_text(), parser="lalr")
transformer = ast_utils.create_transformer(this_module, ToAst())

def parse(text):
    tree = parser.parse(text)
    return transformer.transform(tree)