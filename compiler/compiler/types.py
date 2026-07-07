from dataclasses import dataclass
from typing import Optional
from abc import ABC

@dataclass
class Type(ABC):
    pass


@dataclass
class VoidType(Type):
    def __repr__(self):
        return "Void"


@dataclass
class BoolType(Type):
    def __repr__(self):
        return "Bool"


@dataclass
class IntType(Type):
    def __repr__(self):
        return "Int"

@dataclass
class ClassType(Type):
    cls: 'Class'

    def __repr__(self):
        return f"{self.cls.name}.self"

@dataclass
class ObjectType(Type):
    cls: 'Class'

    def __repr__(self):
        return self.cls.name


@dataclass
class NullType(Type):
    def __repr__(self):
        return "null"


@dataclass
class FunctionType(Type):
    param_types: Optional[list[Type]]  # None means unknown parameters (e.g. from Object)
    return_type: Type

    def __repr__(self):
        if self.param_types is None:
            params = "..."
        else:
            params = ", ".join(str(p) for p in self.param_types)
        return f"({params}) -> {self.return_type}"


def is_assignable_to(source: Type, target: Type) -> bool:
    if source == target:
        return True

    # null can be placed into any object
    if isinstance(source, NullType) and isinstance(target, ObjectType):
        return True

    if isinstance(source, ObjectType) and isinstance(target, ObjectType):
        return source.cls.is_subclass_of(target.cls)

    return False
