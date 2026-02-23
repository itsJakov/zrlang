from dataclasses import dataclass, field
from typing import Union, Optional

from compiler.symbols import FunctionSymbol, ParameterSymbol, FieldSymbol, LocalSymbol, MethodSymbol, Class


@dataclass
class IRReg:
    idx: int

    def __repr__(self):
        return f"%{self.idx}"


IROperand = Union[IRReg, bool, int, str]
IRStorage = Union[LocalSymbol, ParameterSymbol, FieldSymbol]


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
class IRFuncCall:
    func: FunctionSymbol
    args: list[IROperand]
    destination: Optional[IRReg]

    def __repr__(self):
        return f"func_call {self.func.name} ({', '.join(str(a) for a in self.args)}) -> {self.destination}"


@dataclass
class IRVirtualCall:
    method: MethodSymbol
    target: IROperand
    args: list[IROperand]
    destination: Optional[IRReg]

    def __repr__(self):
        return f"virtual_call {self.target} {self.method.name} ({', '.join(str(a) for a in self.args)}) -> {self.destination}"


@dataclass
class IRAlloc:
    cls: Class
    destination: IRReg

    def __repr__(self):
        return f"alloc {self.cls.name} -> {self.destination}"

IRInstruction = Union[IRReturn, IRLoad, IRStore, IRFuncCall, IRVirtualCall, IRAlloc]


@dataclass
class IRFunction:
    sym: FunctionSymbol
    body: list[IRInstruction] = field(default_factory=list)