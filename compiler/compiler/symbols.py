from abc import ABC
from dataclasses import dataclass, field
from typing import Optional, Union

from lang_ast import FuncDecorator
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
    decorators: set[FuncDecorator] = field(default_factory=set)

    def function_type(self) -> FunctionType:
        return FunctionType(
            param_types=[param.type for param in self.params],
            return_type=self.return_type
        )


@dataclass
class Class(Symbol):
    ClassMemberSymbol = Union[FunctionSymbol, PropertySymbol]

    members: dict[str, ClassMemberSymbol]
    parent: Optional['Class'] = None

    def __init__(
        self,
        name: str,
        symbols: Optional[list[ClassMemberSymbol]] = None,
        parent: Optional['Class'] = None
    ):
        super().__init__(name)
        self.members = {}
        self.parent = parent
        if symbols:
            for symbol in symbols:
                self.members[symbol.name] = symbol

    def define(self, symbol: ClassMemberSymbol) -> bool:
        if symbol.name in self.members:
            return False
        self.members[symbol.name] = symbol
        return True

    def is_subclass_of(self, other: 'Class') -> bool:
        if self == other:
            return True
        if self.parent is not None:
            return self.parent.is_subclass_of(other)
        return False

    def lookup_member(self, name: str) -> Optional[ClassMemberSymbol]:
        symbol = self.members.get(name)
        if symbol is not None:
            return symbol
        if self.parent is not None:
            return self.parent.lookup_member(name)
        return None

