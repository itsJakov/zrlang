from abc import ABC
from dataclasses import dataclass, field
from typing import Union, Optional

from compiler.symbols import FunctionSymbol, ParameterSymbol, FieldSymbol, LocalSymbol, MethodSymbol, Class
from compiler.types import Type


@dataclass
class IRReg:
    idx: int
    type: Type

    def __repr__(self):
        return f"%{self.idx}"


IROperand = Union[IRReg, bool, int, str]
IRStorage = Union[LocalSymbol, ParameterSymbol]


@dataclass
class IRReturn:
    value: Optional[IROperand]

    def __repr__(self):
        return f"return {self.value}"


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


def ir_to_str(funcs: list[IRFunction], classes: list[IRClass]) -> str:
    result = ""

    for cls_idx, cls in enumerate(classes):
        result += f"Class {cls.sym.name}:\n"
        for i, method in enumerate(cls.methods):
            result += f"\tMethod {method.sym.name}:\n"
            for instr in method.body:
                result += f"\t\t{instr}\n"
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
            result += f"\t{instr}\n"

    return result
