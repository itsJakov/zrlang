from dataclasses import dataclass, field
from typing import Union, Optional

from compiler.symbols import FunctionSymbol, ParameterSymbol, FieldSymbol, LocalSymbol


@dataclass
class IRReg:
    idx: int


IROperand = Union[IRReg, LocalSymbol, ParameterSymbol, FieldSymbol, bool, int, str]
IRDestination = Union[IRReg, LocalSymbol, ParameterSymbol, FieldSymbol]


@dataclass
class IRReturn:
    value: Optional[IROperand]


IRInstruction = Union[IRReturn]


@dataclass
class IRFunction:
    sym: FunctionSymbol
    body: list[IRInstruction] = field(default_factory=list)