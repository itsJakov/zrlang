from .symbols import Class, MethodSymbol, ParameterSymbol, FunctionSymbol
from .types import VoidType, BoolType, IntType, ObjectType
from .scope import Scope


class StandardTypes:
    OBJECT_CLASS = Class(name="Object", symbols=[])
    STRING_CLASS = Class(name="String", symbols=[])

    STRING_CLASS.parent = OBJECT_CLASS
    STRING_CLASS.define(
        MethodSymbol(
            name="concat",
            is_static=False,
            params=[ParameterSymbol("other", ObjectType(OBJECT_CLASS))],
            return_type=ObjectType(STRING_CLASS),
        )
    )
    OBJECT_CLASS.define(
        MethodSymbol(
            name="toString",
            is_static=False,
            params=[],
            return_type=ObjectType(STRING_CLASS)
        )
    )

    ARRAY_CLASS = Class(
        name="Array",
        parent=OBJECT_CLASS,
        symbols=[
            MethodSymbol(
                name="append",
                is_static=False,
                params=[ParameterSymbol("object", ObjectType(OBJECT_CLASS))],
                return_type=VoidType()
            ),
            MethodSymbol(
                name="get",
                is_static=False,
                params=[ParameterSymbol("index", IntType())],
                return_type=ObjectType(OBJECT_CLASS)
            ),
            MethodSymbol(
                name="getCount",
                is_static=False,
                params=[],
                return_type=IntType()
            ),
            MethodSymbol(
                name="getIsEmpty",
                is_static=False,
                params=[],
                return_type=BoolType()
            ),
        ]
    )

    FILE_CLASS = Class(
        name="File",
        parent=OBJECT_CLASS,
        symbols=[
            MethodSymbol(
                name="initWithPath",
                is_static=False,
                params=[ParameterSymbol(name="path", type=ObjectType(STRING_CLASS))],
                return_type=VoidType()
            ),
            MethodSymbol(
                name="append",
                is_static=False,
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

