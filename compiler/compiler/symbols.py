from abc import ABC
from dataclasses import dataclass
from typing import Optional, Union

from .types import Type, FunctionType


@dataclass
class Symbol(ABC):
    name: str


@dataclass
class LocalSymbol(Symbol):
    type: Type


@dataclass
class PropertySymbol(Symbol):
    type: Type


@dataclass
class ParameterSymbol(Symbol):
    type: Type


@dataclass
class FunctionSymbol(Symbol):
    # FunctionSymbol represents both methods and standalone functions. Not a good idea probably
    params: list[ParameterSymbol]
    return_type: Type

    def function_type(self) -> FunctionType:
        return FunctionType(
            param_types=[param.type for param in self.params],
            return_type=self.return_type
        )


@dataclass
class Class(Symbol):
    ClassMemberSymbol = Union[FunctionSymbol, PropertySymbol]

    symbols: dict[str, ClassMemberSymbol]
    parent: Optional['Class'] = None

    def __init__(
        self,
        name: str,
        symbols: Optional[list[ClassMemberSymbol]] = None,
        parent: Optional['Class'] = None
    ):
        super().__init__(name)
        self.symbols = {}
        self.parent = parent
        if symbols:
            for symbol in symbols:
                self.symbols[symbol.name] = symbol

    def define(self, symbol: ClassMemberSymbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def is_subclass_of(self, other: 'Class') -> bool:
        if self == other:
            return True
        if self.parent is not None:
            return self.parent.is_subclass_of(other)
        return False

    def lookup_member(self, name: str) -> Optional[ClassMemberSymbol]:
        symbol = self.symbols.get(name)
        if symbol is not None:
            return symbol
        if self.parent is not None:
            return self.parent.lookup_member(name)
        return None

