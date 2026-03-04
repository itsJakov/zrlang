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


IROperand = Union[IRReg, IRSelf, bool, int, str]
IRStorage = Union[LocalSymbol, ParameterSymbol]


@dataclass
class IRReturn:
    value: Optional[IROperand]

    def __repr__(self):
        return f"return {self.value}"


@dataclass
class IRBinaryOp:
    op: BinaryOperation
    lhs: IROperand
    rhs: IROperand
    destination: IRReg

    def __repr__(self):
        return f"binary_op {self.lhs} {self.op.value} {self.rhs} -> {self.destination}"


@dataclass
class IRBranch:
    condition: IROperand
    true_block: list['IRInstruction']
    false_block: Optional[list['IRInstruction']]

    def __repr__(self):
        return self._repr_with_indent(0)

    def _repr_with_indent(self, indent: int) -> str:
        tab = "\t" * indent
        true_count = len(self.true_block)
        false_count = len(self.false_block) if self.false_block else 0
        lines = [f"{tab}if {self.condition} then {true_count} instructions else {false_count} instructions"]
        if self.true_block:
            lines.append(f"{tab}[then]")
            for sub in self.true_block:
                if isinstance(sub, IRBranch):
                    lines.append(sub._repr_with_indent(indent + 1))
                else:
                    lines.append("\t" * (indent + 1) + str(sub))
        if self.false_block:
            lines.append(f"{tab}[else]")
            for sub in self.false_block:
                if isinstance(sub, IRBranch):
                    lines.append(sub._repr_with_indent(indent + 1))
                else:
                    lines.append("\t" * (indent + 1) + str(sub))
        return "\n".join(lines)


@dataclass
class IRLoad:
    source: IRStorage
    destination: IRReg

    def __repr__(self):
        return f"load {self.source.name} -> {self.destination}"


@dataclass
class IRStore:
    value: IROperand
    destination: IRStorage

    def __repr__(self):
        return f"store {self.value} -> {self.destination}"


@dataclass
class IRLoadField:
    target: IROperand
    field: FieldSymbol
    destination: Optional[IRReg]

    def __repr__(self):
        return f"load_field {self.target} {self.field.name} -> {self.destination}"


@dataclass
class IRStoreField:
    value: IROperand
    target: IROperand
    field: FieldSymbol

    def __repr__(self):
        return f"store_field {self.value} -> {self.target} {self.field.name}"


@dataclass
class _IRCall(ABC):
    args: list[IROperand]
    destination: Optional[IRReg]


@dataclass
class IRFuncCall(_IRCall):
    func: FunctionSymbol

    def __repr__(self):
        return f"func_call {self.func.name} ({', '.join(str(a) for a in self.args)}) -> {self.destination}"


@dataclass
class IRStaticCall(_IRCall):
    cls: Class
    method: MethodSymbol

    def __repr__(self):
        return f"static_call {self.cls.name} {self.method.name} ({', '.join(str(a) for a in self.args)}) -> {self.destination}"


@dataclass
class IRVirtualCall(_IRCall):
    method: MethodSymbol
    target: IROperand

    def __repr__(self):
        return f"virtual_call {self.target} {self.method.name} ({', '.join(str(a) for a in self.args)}) -> {self.destination}"


@dataclass
class IRSuperCall(_IRCall):
    cls: Class
    method: MethodSymbol

    def __repr__(self):
        return f"super_call {self.cls.name} {self.method.name} ({', '.join(str(a) for a in self.args)}) -> {self.destination}"


@dataclass
class IRAlloc:
    cls: Class
    destination: IRReg

    def __repr__(self):
        return f"alloc {self.cls.name} -> {self.destination}"


IRInstruction = Union[
    IRReturn,
    IRBinaryOp,
    IRBranch,
    IRLoad, IRStore,
    IRLoadField, IRStoreField,
    IRFuncCall, IRStaticCall, IRVirtualCall, IRSuperCall,
    IRAlloc
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


def instr_to_str(instr: 'IRInstruction', indent: int) -> str:
    if isinstance(instr, IRBranch):
        return instr._repr_with_indent(indent)
    tab = "\t" * indent
    return f"{tab}{instr}"


def ir_to_str(funcs: list[IRFunction], classes: list[IRClass]) -> str:
    result = ""

    for cls_idx, cls in enumerate(classes):
        result += f"Class {cls.sym.name}:\n"
        for i, method in enumerate(cls.methods):
            result += f"\tMethod {method.sym.name}:\n"
            for instr in method.body:
                result += instr_to_str(instr, 2) + "\n"
            # Add newline after each method except the last one in the class
            if i < len(cls.methods) - 1:
                result += "\n"

        # Add newline after each class except the last one
        if cls_idx < len(classes) - 1:
            result += "\n"

    # Add newline between classes and functions if both exist
    if classes and funcs:
        result += "\n"

    for func in funcs:
        result += f"Function {func.sym.name}:\n"
        for instr in func.body:
            result += instr_to_str(instr, 1) + "\n"

    return result
