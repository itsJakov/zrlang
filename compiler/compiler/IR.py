from abc import ABC
from dataclasses import dataclass, field
from typing import Union, Optional

from compiler.symbols import FunctionSymbol, ParameterSymbol, FieldSymbol, LocalSymbol, MethodSymbol, Class
from compiler.types import Type
from lang_ast import BinaryOperation


@dataclass
class IRReg:
    idx: int
    type: Type

    def __repr__(self):
        return f"%{self.idx}"


@dataclass
class IRSelf:
    def __repr__(self):
        return "%self"


@dataclass
class IRNull:
    def __repr__(self):
        return "null"


IROperand = Union[IRReg, IRSelf, IRNull, bool, int]
IRStorage = Union[LocalSymbol, ParameterSymbol]


@dataclass
class IRReturn:
    value: Optional[IROperand]

    def __repr__(self):
        return "return" if self.value is None else f"return {_fmt(self.value)}"


@dataclass
class IRBinaryOp:
    op: BinaryOperation
    lhs: IROperand
    rhs: IROperand
    destination: IRReg

    def __repr__(self):
        return f"{_fmt(self.destination)} = {_fmt(self.lhs)} {self.op.value} {_fmt(self.rhs)}"


@dataclass
class IRBranch:
    condition: IROperand
    true_block: list['IRInstruction']
    false_block: Optional[list['IRInstruction']]

    def __repr__(self):
        else_part = "" if self.false_block is None else " else { ... }"
        return f"if {_fmt(self.condition)} {{ ... }}{else_part}"


@dataclass
class IRLoop:
    body: list['IRInstruction']

    def __repr__(self):
        return "loop { ... }"


@dataclass
class IRBreak:
    def __repr__(self):
        return "break"


@dataclass
class IRContinue:
    def __repr__(self):
        return "continue"


@dataclass
class IRLoad:
    source: IRStorage
    destination: IRReg

    def __repr__(self):
        return f"{_fmt(self.destination)} = load {self.source.name}"


@dataclass
class IRStore:
    value: IROperand
    destination: IRStorage

    def __repr__(self):
        return f"store {_fmt(self.value)} -> {self.destination.name}"


@dataclass
class IRLoadField:
    target: IROperand
    field: FieldSymbol
    destination: Optional[IRReg]

    def __repr__(self):
        dst = "_" if self.destination is None else _fmt(self.destination)
        return f"{dst} = load {_fmt(self.target)}.{self.field.name}"


@dataclass
class IRStoreField:
    value: IROperand
    target: IROperand
    field: FieldSymbol

    def __repr__(self):
        return f"store {_fmt(self.value)} -> {_fmt(self.target)}.{self.field.name}"


@dataclass
class _IRCall(ABC):
    args: list[IROperand]
    destination: Optional[IRReg]


@dataclass
class IRFuncCall(_IRCall):
    func: FunctionSymbol

    def __repr__(self):
        return _fmt_call(self.destination, self.func.name, self.args)


@dataclass
class IRStaticCall(_IRCall):
    cls: Class
    method: MethodSymbol

    def __repr__(self):
        return _fmt_call(self.destination, f"{self.cls.name}::{self.method.name}", self.args)


@dataclass
class IRVirtualCall(_IRCall):
    method: MethodSymbol
    target: IROperand

    def __repr__(self):
        return _fmt_call(self.destination, f"{_fmt(self.target)}.{self.method.name}", self.args)


@dataclass
class IRSuperCall(_IRCall):
    cls: Class
    method: MethodSymbol

    def __repr__(self):
        return _fmt_call(self.destination, f"super.{self.method.name}", self.args)


@dataclass
class IRRetain:
    obj: IRReg

    def __repr__(self):
        return f"retain {_fmt(self.obj)}"


@dataclass
class IRRelease:
    obj: IRReg

    def __repr__(self):
        return f"release {_fmt(self.obj)}"


@dataclass
class IRAlloc:
    cls: Class
    destination: IRReg

    def __repr__(self):
        return f"{_fmt(self.destination)} = alloc {self.cls.name}"


@dataclass
class IRStringLiteral:
    value: str
    destination: IRReg

    def __repr__(self):
        return f'{_fmt(self.destination)} = "{self.value}"'


@dataclass
class IRCheckDowncast:
    obj: IRReg
    cls: Class

    def __repr__(self):
        return f"check_cast {_fmt(self.obj)}"


IRInstruction = Union[
    IRReturn,
    IRBinaryOp,
    IRBranch,
    IRLoop, IRBreak, IRContinue,
    IRLoad, IRStore,
    IRLoadField, IRStoreField,
    IRFuncCall, IRStaticCall, IRVirtualCall, IRSuperCall,
    IRRetain, IRRelease,
    IRAlloc, IRStringLiteral,
    IRCheckDowncast,
]


@dataclass
class IRFunction:
    sym: FunctionSymbol
    body: list[IRInstruction] = field(default_factory=list)
    locals: list[LocalSymbol] = field(default_factory=list)


@dataclass
class IRMethod(IRFunction):
    sym: MethodSymbol


@dataclass
class IRClass:
    sym: Class
    methods: list[IRMethod] = field(default_factory=list)


# -- Pretty printer (vibe coded) --
_INDENT = "    "


def _fmt(op: IROperand) -> str:
    if isinstance(op, bool):
        return "true" if op else "false"
    return str(op)


def _fmt_args(args: list[IROperand]) -> str:
    return ", ".join(_fmt(a) for a in args)


def _fmt_call(dest: Optional[IRReg], callee: str, args: list[IROperand]) -> str:
    call = f"{callee}({_fmt_args(args)})"
    return call if dest is None else f"{_fmt(dest)} = {call}"


def _fmt_block_lines(body: list[IRInstruction], indent: int) -> list[str]:
    out: list[str] = []
    for instr in body:
        if isinstance(instr, IRBranch):
            out.extend(_fmt_branch_lines(instr, indent))
        elif isinstance(instr, IRLoop):
            out.extend(_fmt_loop_lines(instr, indent))
        else:
            out.append(_INDENT * indent + repr(instr))
    return out


def _fmt_branch_lines(branch: IRBranch, indent: int) -> list[str]:
    pad = _INDENT * indent
    lines = [f"{pad}if {_fmt(branch.condition)} {{"]
    lines.extend(_fmt_block_lines(branch.true_block, indent + 1))
    if branch.false_block is None:
        lines.append(f"{pad}}}")
    else:
        lines.append(f"{pad}}} else {{")
        lines.extend(_fmt_block_lines(branch.false_block, indent + 1))
        lines.append(f"{pad}}}")
    return lines


def _fmt_loop_lines(loop: IRLoop, indent: int) -> list[str]:
    pad = _INDENT * indent
    lines = [f"{pad}loop {{"]
    lines.extend(_fmt_block_lines(loop.body, indent + 1))
    lines.append(f"{pad}}}")
    return lines


def _fmt_signature(sym) -> str:
    return ", ".join(p.name for p in sym.params)


def ir_to_str(funcs: list[IRFunction], classes: list[IRClass]) -> str:
    sections: list[str] = []

    for func in funcs:
        lines = [f"function {func.sym.name}({_fmt_signature(func.sym)}) {{"]
        lines.extend(_fmt_block_lines(func.body, 1))
        lines.append("}")
        sections.append("\n".join(lines))

    for cls in classes:
        lines = [f"class {cls.sym.name} {{"]
        method_blocks: list[list[str]] = []
        for method in cls.methods:
            kw = "static method" if method.sym.is_static else "method"
            mlines = [f"{_INDENT}{kw} {method.sym.name}({_fmt_signature(method.sym)}) {{"]
            mlines.extend(_fmt_block_lines(method.body, 2))
            mlines.append(f"{_INDENT}}}")
            method_blocks.append(mlines)

        for i, mblock in enumerate(method_blocks):
            if i > 0:
                lines.append("")
            lines.extend(mblock)
        lines.append("}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections) + "\n"
