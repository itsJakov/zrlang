from dataclasses import dataclass, field
from typing import Union, Optional

from compiler.symbols import FunctionSymbol, ParameterSymbol, FieldSymbol, LocalSymbol, MethodSymbol


@dataclass
class IRReg:
    idx: int


IROperand = Union[IRReg, LocalSymbol, ParameterSymbol, FieldSymbol, bool, int, str]
IRDestination = Union[IRReg, LocalSymbol, ParameterSymbol, FieldSymbol]


@dataclass
class IRReturn:
    value: Optional[IROperand]

    def __repr__(self):
        return f"return {self.value}"

@dataclass
class IRFuncCall:
    func: FunctionSymbol
    args: list[IROperand]
    destination: Optional[IRDestination]

    def __repr__(self):
        return f"func_call {self.func.name} ({', '.join(str(a) for a in self.args)}) -> {self.destination}"


@dataclass
class IRVirtualCall:
    method: MethodSymbol
    target: IROperand
    args: list[IROperand]
    destination: Optional[IRDestination]

    def __repr__(self):
        return f"virtual_call on {self.target} {self.method.name} ({', '.join(str(a) for a in self.args)}) -> {self.destination}"

IRInstruction = Union[IRReturn, IRFuncCall, IRVirtualCall]


@dataclass
class IRFunction:
    sym: FunctionSymbol
    body: list[IRInstruction] = field(default_factory=list)