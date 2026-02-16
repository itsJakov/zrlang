from .symbols import Class, FunctionSymbol, ParameterSymbol
from .types import VoidType, BoolType, IntType, ObjectType
from .scope import Scope


class StandardTypes:
    OBJECT_CLASS = Class(name="Object", symbols=[])
    STRING_CLASS = Class(name="String", symbols=[])

    STRING_CLASS.parent = OBJECT_CLASS
    STRING_CLASS.define(
        FunctionSymbol(
            name="concat",
            params=[ParameterSymbol("other", ObjectType(OBJECT_CLASS))],
            return_type=ObjectType(STRING_CLASS)
        )
    )
    OBJECT_CLASS.define(
        FunctionSymbol(
            name="toString",
            params=[],
            return_type=ObjectType(STRING_CLASS)
        )
    )

    ARRAY_CLASS = Class(
        name="Array",
        parent=OBJECT_CLASS,
        symbols=[
            FunctionSymbol(
                name="append",
                params=[ParameterSymbol("object", ObjectType(OBJECT_CLASS))],
                return_type=VoidType()
            ),
            FunctionSymbol(
                name="get",
                params=[ParameterSymbol("index", IntType())],
                return_type=ObjectType(OBJECT_CLASS)
            ),
            FunctionSymbol(
                name="getIsEmpty",
                params=[],
                return_type=BoolType()
            ),
        ]
    )

    FILE_CLASS = Class(
        name="File",
        parent=OBJECT_CLASS,
        symbols=[
            FunctionSymbol(
                name="initWithPath",
                params=[ParameterSymbol(name="path", type=ObjectType(STRING_CLASS))],
                return_type=VoidType()
            ),
            FunctionSymbol(
                name="append",
                params=[ParameterSymbol(name="content", type=ObjectType(STRING_CLASS))],
                return_type=VoidType()
            ),
        ]
    )

    PRINT_FUNCTION = FunctionSymbol(
        name="print",
        params=[ParameterSymbol(name="value", type=ObjectType(OBJECT_CLASS))],
        return_type=VoidType()
    )

    @staticmethod
    def create_global_scope() -> Scope:
        scope = Scope()
        scope.define(StandardTypes.OBJECT_CLASS)
        scope.define(StandardTypes.STRING_CLASS)
        scope.define(StandardTypes.ARRAY_CLASS)
        scope.define(StandardTypes.FILE_CLASS)
        scope.define(StandardTypes.PRINT_FUNCTION)
        return scope

