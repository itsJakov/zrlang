import sys
from dataclasses import dataclass, field
from typing import Optional, Union

from lang_ast import ClassDecl, ClassField, MethodDecl, _Expression, IntExpr, StringExpr, SymbolExpr, MemberExpr, \
    CallExpr, BinaryExpr, BinaryOperation, _Statement, VarStmt, ExprStmt, AssignStmt, IfStmt, AllocExpr, _Ast


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

@dataclass
class VoidType:
    pass

@dataclass
class BoolType:
    pass

@dataclass
class IntType:
    pass

@dataclass
class ObjectType:
    cls: 'Class'

@dataclass
class FunctionType:
    param_types: list['Type']
    return_type: 'Type'

Type = Union[VoidType, BoolType, IntType, ObjectType, FunctionType]

@dataclass
class Symbol:
    name: str

@dataclass
class VariableSymbol(Symbol):
    type: Type

@dataclass
class FunctionSymbol(Symbol):
    type: FunctionType

@dataclass
class Class(Symbol):
    methods: dict[str, FunctionType] = field(default_factory=dict)
    fields: dict[str, Type] = field(default_factory=dict)
    parent: Optional['Class'] = None

class StandardTypes:
    STRING_CLASS = Class(
        name="String",
        methods={
            "printToStdout": FunctionType(param_types=[], return_type=VoidType()),
        }
    )

    OBJECT_CLASS = Class(
        name="RootObject",
        methods={
            "toString": FunctionType(param_types=[], return_type=ObjectType(cls=STRING_CLASS)),
        }
    )

    ARRAY_CLASS = Class(
        name="Array",
        methods={
            "append": FunctionType(param_types=[], return_type=VoidType()),
            "get": FunctionType(param_types=[], return_type=ObjectType(cls=OBJECT_CLASS)),
            "getIsEmpty": FunctionType(param_types=[], return_type=BoolType()),
        }
    )

    PRINT_FUNCTION = FunctionSymbol(name="print", type=FunctionType(param_types=[], return_type=VoidType()))

class Scope:
    def __init__(self, parent: Optional['Scope'] = None):
        self.parent: Optional[Scope] = parent
        self.symbols: dict[str, Symbol] = {}

    def define(self, symbol: Symbol):
        if symbol.name in self.symbols:
            eprint(f"Symbol {symbol.name} already defined in this scope")
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        symbol = self.symbols.get(name)
        if symbol is not None:
            return symbol
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    @staticmethod
    def global_scope() -> 'Scope':
        scope = Scope()
        scope.define(StandardTypes.STRING_CLASS)
        scope.define(StandardTypes.ARRAY_CLASS)
        scope.define(StandardTypes.OBJECT_CLASS)
        scope.define(StandardTypes.PRINT_FUNCTION)

        scope.define(Class(name="User", fields={"username": ObjectType(cls=StandardTypes.STRING_CLASS)}))
        return scope


class SemanticAnalyzer:
    def __init__(self, source_name: str = "<input>"):
        self.scope = Scope.global_scope()
        self.source_name = source_name

    def _format_location(self, node: Optional[_Ast]) -> str:
        if node is None or node.meta is None:
            return f"{self.source_name}:?:?: "

        line = node.meta.line or "?"
        column = node.meta.column or "?"
        return f"{self.source_name}:{line}:{column}: "

    def _error(self, message: str, node=None):
        location = self._format_location(node)
        eprint(f"{location}error: {message}")

    def _warning(self, message: str, node=None):
        location = self._format_location(node)
        eprint(f"{location}warning: {message}")

    def push_scope(self) -> Scope:
        new_scope = Scope(parent=self.scope)
        self.scope = new_scope
        return new_scope

    def pop_scope(self):
        if self.scope.parent is not None:
            self.scope = self.scope.parent
        else:
            raise Exception("Cannot pop global scope")

    def analyze(self, ast: list[ClassDecl]) -> bool:
        # Pass 1: Collect class information
        for cls_decl in ast:
            self._collect_class_info(cls_decl)

        # Pass 2: Verify class hierarchies

        # Pass 3: Verify methods
        for cls_decl in ast:
            for member in cls_decl.members:
                if isinstance(member, MethodDecl):
                    self._analyze_method(cls_decl, member)

        return True

    def _collect_class_info(self, cls: ClassDecl):
        class_obj = Class(name=cls.name)

        for member in cls.members:
            if isinstance(member, ClassField):
                field_type = self._resolve_type_name(member.type, member)
                class_obj.fields[member.name] = field_type
            elif isinstance(member, MethodDecl):
                method_type = FunctionType(param_types=[], return_type=VoidType())
                class_obj.methods[member.name] = method_type
            else:
                self._error(f"Unknown class member type: {type(member)}", member)

        self.scope.define(class_obj)

    # TODO: Do this properly
    def _resolve_type_name(self, type_name: str, node=None) -> Type:
        if type_name == "Int":
            return IntType()
        elif type_name == "Bool":
            return BoolType()
        elif type_name == "Void":
            return VoidType()

        symbol = self.scope.lookup(type_name)
        if isinstance(symbol, Class):
            return ObjectType(cls=symbol)

        self._error(f"Unknown type: {type_name}", node)
        return VoidType()

    def _analyze_method(self, cls_decl: ClassDecl, method: MethodDecl):
        self.push_scope()
        # TODO: Add parameters to scope
        cls = self.scope.lookup(cls_decl.name)
        if not isinstance(cls, Class):
            self._error("internal error: method's class not found in scope", method)
            sys.exit(1)

        self.scope.define(VariableSymbol(name="self", type=ObjectType(cls=cls)))
        self._analyze_block(method.block)
        self.pop_scope()

    def _analyze_block(self, block: list[_Statement]):
        self.push_scope()
        for stmt in block:
            self._analyze_statement(stmt)
        self.pop_scope()

    def _analyze_statement(self, stmt: _Statement):
        if isinstance(stmt, VarStmt):
            value_type = self._analyze_expression(stmt.expr)
            self.scope.define(VariableSymbol(name=stmt.local, type=value_type))

        if isinstance(stmt, ExprStmt):
            self._analyze_expression(stmt.expr)

        if isinstance(stmt, AssignStmt):
            assignee_type = self._analyze_expression(stmt.assignee)
            value_type = self._analyze_expression(stmt.value)
            if assignee_type != value_type:
                self._error(f"Type mismatch in assignment: {type(assignee_type).__name__} and {type(value_type).__name__}", stmt)

        if isinstance(stmt, IfStmt):
            condition_type = self._analyze_expression(stmt.condition)
            if not isinstance(condition_type, BoolType):
                self._error(f"If condition must be of type Bool, got {type(condition_type).__name__}", stmt)
            self._analyze_block(stmt.block)
            if stmt.else_block is not None:
                self._analyze_block(stmt.else_block)

    def _analyze_expression(self, expr: _Expression) -> Optional[Type]:
        if isinstance(expr, IntExpr):
            return IntType()

        if isinstance(expr, StringExpr):
            return ObjectType(cls=StandardTypes.STRING_CLASS)

        if isinstance(expr, SymbolExpr):
            symbol = self.scope.lookup(expr.name)
            if symbol is None:
                self._error(f"Undefined symbol {expr.name}", expr)
                return None
            if isinstance(symbol, VariableSymbol):
                return symbol.type
            if isinstance(symbol, FunctionSymbol):
                return symbol.type
            if isinstance(symbol, Class):
                # TODO: Static access (and reflection one day)
                self._error(f"{expr.name} is a type name, not a value", expr)
                return None
            self._error(f"{expr.name} cannot be used as an expression", expr)
            return None

        if isinstance(expr, MemberExpr):
            target_type = self._analyze_expression(expr.expr)

            if isinstance(target_type, ObjectType):
                field_type = target_type.cls.fields.get(expr.member)
                if field_type is not None:
                    return field_type

                method_type = target_type.cls.methods.get(expr.member)
                if method_type is not None:
                    return method_type

                if target_type.cls == StandardTypes.OBJECT_CLASS:
                    # Just like Objective-C >:)
                    self._warning(f"Accessing undefined method {expr.member} on Object, assuming it returns Object", expr)
                    return FunctionType(param_types=[], return_type=ObjectType(cls=StandardTypes.OBJECT_CLASS))

                self._error(f"Undefined member {expr.member} on class {target_type.cls.name}", expr)
                return None

            self._error(f"Member access not supported on type {type(target_type).__name__}", expr)
            return None

        if isinstance(expr, CallExpr):
            callee_type = self._analyze_expression(expr.callee)

            if isinstance(callee_type, FunctionType):
                # TODO: Type check arguments against parameter types
                for arg in expr.args:
                    self._analyze_expression(arg)
                return callee_type.return_type

            self._error(f"Attempting to call non-callable type {type(callee_type).__name__}", expr)
            return None

        if isinstance(expr, BinaryExpr):
            lhs_type = self._analyze_expression(expr.lhs)
            rhs_type = self._analyze_expression(expr.rhs)

            if type(lhs_type) != type(rhs_type):
                self._error(f"Type mismatch in binary expression: {type(lhs_type).__name__} and {type(rhs_type).__name__}", expr)
                return None

            match expr.op:
                case BinaryOperation.ADD | BinaryOperation.SUB | BinaryOperation.MUL | BinaryOperation.DIV | BinaryOperation.MOD:
                    if isinstance(lhs_type, IntType):
                        return IntType()
                    else:
                        self._error(f"Arithmetic operations only supported on Int, got {type(lhs_type).__name__}", expr)
                        return None
                case BinaryOperation.EQ | BinaryOperation.NEQ | BinaryOperation.GT | BinaryOperation.GTE | BinaryOperation.LT | BinaryOperation.LTE:
                    if isinstance(lhs_type, IntType):
                        return BoolType()
                    else:
                        self._error(f"Comparison operations only supported on Int, got {type(lhs_type).__name__}", expr)
                        return None
                case BinaryOperation.AND | BinaryOperation.OR:
                    self._error(f"Logical operators not supported yet!", expr)
                    return None

        if isinstance(expr, AllocExpr):
            class_symbol = self.scope.lookup(expr.cls_name)
            if class_symbol is None:
                self._error(f"Undefined class {expr.cls_name}", expr)
                return None
            if not isinstance(class_symbol, Class):
                self._error(f"{expr.cls_name} is not a class", expr)
                return None
            return ObjectType(cls=class_symbol)

        self._error(f"Unknown expression type: {type(expr).__name__}", expr)
        return None
