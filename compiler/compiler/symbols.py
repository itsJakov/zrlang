from abc import ABC
from dataclasses import dataclass
from typing import Optional

from .types import Type, FunctionType


@dataclass
class Symbol(ABC):
    name: str

@dataclass
class LocalSymbol(Symbol):
    type: Type
    node: Optional['VarStmt'] = None

    def __hash__(self):
        return id(self)


@dataclass
class ParameterSymbol(Symbol):
    type: Type
    node: Optional['FuncParam'] = None


@dataclass
class FunctionSymbol(Symbol):
    params: list[ParameterSymbol]
    return_type: Type
    node: Optional['FuncDecl'] = None

    def function_type(self) -> FunctionType:
        return FunctionType(
            param_types=[param.type for param in self.params],
            return_type=self.return_type
        )

@dataclass
class ClassMemberSymbol(Symbol, ABC):
    is_static: bool

@dataclass
class FieldSymbol(ClassMemberSymbol):
    type: Type
    node: Optional['ClassField'] = None

@dataclass
class MethodSymbol(FunctionSymbol, ClassMemberSymbol):
    pass


@dataclass
class Class(Symbol):
    members: dict[str, ClassMemberSymbol]
    parent: Optional['Class'] = None
    node: Optional['ClassDecl'] = None

    def __init__(
        self,
        name: str,
        symbols: Optional[list[ClassMemberSymbol]] = None,
        parent: Optional['Class'] = None,
        node: Optional['ClassDecl'] = None
    ):
        super().__init__(name)
        self.members = {}
        self.parent = parent
        self.node = node
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

