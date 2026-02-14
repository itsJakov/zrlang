import sys
from dataclasses import dataclass, field
from typing import Optional, Union

from lang_ast import ClassDecl, ClassField, FuncDecl, _Expression, IntExpr, StringExpr, SymbolExpr, MemberExpr, \
    CallExpr, BinaryExpr, BinaryOperation, _Statement, VarStmt, ExprStmt, AssignStmt, IfStmt, AllocExpr, _Ast, \
    ReturnStmt, BoolExpr, _TopLevelDecl, FuncDecorator


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

@dataclass
class VoidType:
    def __repr__(self):
        return "Void"

@dataclass
class BoolType:
    def __repr__(self):
        return "Bool"

@dataclass
class IntType:
    def __repr__(self):
        return "Int"

@dataclass
class ObjectType:
    cls: 'Class'

    def __repr__(self):
        return self.cls.name

@dataclass
class FunctionType:
    param_types: Optional[list['Type']] # None means unknown parameters (e.g. from Object)
    return_type: 'Type'

    def __repr__(self):
        if self.param_types is None:
            params = "..."
        else:
            params = ", ".join(str(p) for p in self.param_types)
        return f"({params}) -> {self.return_type}"

Type = Union[VoidType, BoolType, IntType, ObjectType, FunctionType]

def is_assignable_to(source: Type, target: Type) -> bool:
    if source == target:
        return True

    if isinstance(source, ObjectType) and isinstance(target, ObjectType):
        return source.cls.is_subclass_of(target.cls)

    return False

@dataclass
class Symbol:
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
    params: list[ParameterSymbol]
    return_type: Type

    def function_type(self) -> FunctionType:
        return FunctionType(param_types=[param.type for param in self.params], return_type=self.return_type)

@dataclass
class Class(Symbol):
    ClassMemberSymbol = FunctionSymbol | PropertySymbol

    symbols: dict[str, ClassMemberSymbol]
    parent: Optional['Class'] = None

    def __init__(self, name: str, symbols: Optional[list[ClassMemberSymbol]] = None, parent: Optional['Class'] = None):
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

class StandardTypes:
    STRING_CLASS = Class(name="String", symbols=[])
    OBJECT_CLASS = Class(name="Object", symbols=[])

    # Dependency loop...
    STRING_CLASS.parent = OBJECT_CLASS
    STRING_CLASS.define(FunctionSymbol(name="concat", params=[ParameterSymbol("other", ObjectType(OBJECT_CLASS))], return_type=ObjectType(STRING_CLASS)))
    OBJECT_CLASS.define(FunctionSymbol(name="toString", params=[], return_type=ObjectType(STRING_CLASS)))

    ARRAY_CLASS = Class(
        name="Array",
        parent=OBJECT_CLASS,
        symbols=[
            FunctionSymbol(name="append", params=[ParameterSymbol("object", ObjectType(OBJECT_CLASS))], return_type=VoidType()),
            FunctionSymbol(name="get", params=[ParameterSymbol("index", IntType())], return_type=ObjectType(OBJECT_CLASS)),
            FunctionSymbol(name="getIsEmpty", params=[], return_type=BoolType()),
        ]
    )

    FILE_CLASS = Class(
        name="File",
        parent=OBJECT_CLASS,
        symbols=[
            FunctionSymbol(name="initWithPath", params=[ParameterSymbol(name="path", type=ObjectType(cls=STRING_CLASS))], return_type=VoidType()),
            FunctionSymbol(name="append", params=[ParameterSymbol(name="content", type=ObjectType(cls=STRING_CLASS))], return_type=VoidType()),
        ]
    )

    PRINT_FUNCTION = FunctionSymbol(name="print", params=[ParameterSymbol(name="value", type=ObjectType(OBJECT_CLASS))], return_type=VoidType())

class Scope:
    def __init__(self, parent: Optional['Scope'] = None):
        self.parent: Optional[Scope] = parent
        self.symbols: dict[str, Symbol] = {}
        self.return_type: Optional[Type] = None

    def define(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

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
        scope.define(StandardTypes.FILE_CLASS)
        scope.define(StandardTypes.PRINT_FUNCTION)
        return scope


class SemanticAnalyzer:
    def __init__(self, source_name: str = "<input>"):
        self.scope = Scope.global_scope()
        self.source_name = source_name
        self.error_count = 0

    def _format_location(self, node: Optional[_Ast]) -> str:
        if node is None or node.meta is None:
            return f"{self.source_name}:?:?: "

        line = node.meta.line or "?"
        column = node.meta.column or "?"
        return f"{self.source_name}:{line}:{column}: "

    def _error(self, message: str, node=None):
        self.error_count += 1
        location = self._format_location(node)
        eprint(f"{location}error: {message}")

    def _warning(self, message: str, node=None):
        location = self._format_location(node)
        eprint(f"{location}warning: {message}")

    def push_scope(self) -> Scope:
        new_scope = Scope(parent=self.scope)
        # TODO: Probably should find a better way to handle return/break/continue scopes
        new_scope.return_type = self.scope.return_type
        self.scope = new_scope
        return new_scope

    def pop_scope(self):
        if self.scope.parent is not None:
            self.scope = self.scope.parent
        else:
            raise Exception("Cannot pop global scope")

    def analyze(self, ast: list[_TopLevelDecl]) -> bool:
        # Pass 1: Collect function and class symbols
        for decl in ast:
            if isinstance(decl, FuncDecl):
                func_symbol = self._function_symbol(decl)
                if not self.scope.define(func_symbol):
                    self._error(f"Function '{func_symbol.name}' is already defined", decl)
            elif isinstance(decl, ClassDecl):
                class_symbol = self._class_symbol(decl)
                if not self.scope.define(class_symbol):
                    self._error(f"Class '{class_symbol.name}' is already defined", decl)

        # Pass 2: Resolve class hierarchies
        for decl in ast:
            if isinstance(decl, ClassDecl):
                self._resolve_class_hierarchy(decl)

        # Pass 3: Verify methods
        for decl in ast:
            if isinstance(decl, FuncDecl):
                self._analyze_function(decl)
            elif isinstance(decl, ClassDecl):
                self._analyze_class(decl)

        return self.error_count == 0

    def _resolve_class_hierarchy(self, cls_decl: ClassDecl):
        class_sym = self.scope.lookup(cls_decl.name)
        if not isinstance(class_sym, Class):
            return

        if cls_decl.super is None:
            class_sym.parent = StandardTypes.OBJECT_CLASS
            return

        parent_sym = self.scope.lookup(cls_decl.super)
        if parent_sym is None:
            self._error(f"Unknown parent class '{cls_decl.super}'", cls_decl)
            return
        if not isinstance(parent_sym, Class):
            self._error(f"'{cls_decl.super}' is not a class", cls_decl)
            return

        class_sym.parent = parent_sym

    def _function_symbol(self, func: FuncDecl) -> FunctionSymbol:
        params = []
        for param in func.params:
            param.type = self._resolve_type_name(param.type_name, param)
            params.append(ParameterSymbol(name=param.name, type=param.type))

        func.return_type = VoidType()
        if func.return_type_name is not None:
            func.return_type = self._resolve_type_name(func.return_type_name, func)

        return FunctionSymbol(name=func.name, params=params, return_type=func.return_type)

    def _class_symbol(self, cls: ClassDecl) -> Class:
        class_sym = Class(name=cls.name)

        for member in cls.members:
            if isinstance(member, ClassField):
                field_type = self._resolve_type_name(member.type, member)
                if not class_sym.define(PropertySymbol(name=member.name, type=field_type)):
                    self._error(f"Member '{member.name}' is already defined in class '{cls.name}'", member)
            elif isinstance(member, FuncDecl):
                if not class_sym.define(self._function_symbol(member)):
                    self._error(f"Member '{member.name}' is already defined in class '{cls.name}'", member)
            else:
                self._error(f"Unknown class member type: {type(member)}", member)

        return class_sym

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

    def _analyze_function(self, func_decl: FuncDecl, self_type: Optional[ObjectType] = None):
        self.push_scope()

        if self_type is not None:
            self.scope.define(ParameterSymbol(name="self", type=self_type))

        for param in func_decl.params:
            if not self.scope.define(ParameterSymbol(name=param.name, type=param.type)):
                self._error(f"Parameter '{param.name}' is already defined", param)
        self.scope.return_type = func_decl.return_type

        self._analyze_block(func_decl.block)
        self.pop_scope()

    def _analyze_class(self, cls_decl: ClassDecl):
        cls = self.scope.lookup(cls_decl.name)
        if not isinstance(cls, Class):
            self._error("internal error: class not found in scope", cls_decl)
            sys.exit(1)

        self._check_method_overrides(cls, cls_decl)

        self_type = ObjectType(cls=cls)
        for member in cls_decl.members:
            if isinstance(member, FuncDecl):
                self._analyze_function(member, self_type=self_type)

    def _check_method_overrides(self, cls: Class, cls_decl: ClassDecl):
        for member in cls_decl.members:
            if not isinstance(member, FuncDecl):
                continue
            func_decl: FuncDecl = member
            is_override = FuncDecorator.OVERRIDE in func_decl.decorators

            symbol = cls.lookup_member(member.name)
            if symbol is None or not isinstance(symbol, FunctionSymbol):
                continue # Should never happen

            # Error 1: Class has no parent but method has override keyword
            if cls.parent is None or cls.parent == StandardTypes.OBJECT_CLASS:
                if is_override:
                    self._error(f"Method '{func_decl.name}' has 'override' but class has no parent", func_decl)
                continue

            # Error 2: Method has override keyword but does not override any parent method
            parent_symbol = cls.parent.lookup_member(func_decl.name)
            if parent_symbol is None:
                if is_override:
                    self._error(f"Method '{func_decl.name}' has 'override' but does not override any parent method", func_decl)
                continue

            # Error 3: Method overrides a method without override keyword
            if not is_override:
                self._error(f"Method '{func_decl.name}' overrides parent method but missing 'override'", func_decl)

            # Error 4: Method signature does not match parent method signature
            if len(symbol.params) != len(parent_symbol.params):
                self._error(
                    f"Method '{symbol.name}' has {len(symbol.params)} parameter(s), "
                    f"but parent method has {len(parent_symbol.params)}",
                    func_decl
                )
                continue

            # TODO: Does contravariance make sense for parameters?
            # Check parameter types (contravariance: parent param type should be assignable to child param type)
            for i, (child_param, parent_param) in enumerate(zip(symbol.params, parent_symbol.params)):
                if not is_assignable_to(parent_param.type, child_param.type):
                    self._error(
                        f"Method '{symbol.name}' parameter {i + 1} type '{child_param.type}' is not compatible "
                        f"with parent parameter type '{parent_param.type}'",
                        func_decl
                    )

            # Check return type (covariance: child return type should be assignable to parent return type)
            if not is_assignable_to(symbol.return_type, parent_symbol.return_type):
                self._error(
                    f"Method '{symbol.name}' return type '{symbol.return_type}' is not compatible "
                    f"with parent return type '{parent_symbol.return_type}'",
                    func_decl
                )

    def _analyze_block(self, block: list[_Statement]):
        self.push_scope()
        for stmt in block:
            if isinstance(stmt, ReturnStmt):
                value_type = VoidType()
                if stmt.expr is not None:
                    value_type = self._analyze_expression(stmt.expr)

                if not is_assignable_to(value_type, self.scope.return_type):
                    self._error(f"Return type mismatch: expected {self.scope.return_type}, got {value_type}", stmt)
                continue
            self._analyze_statement(stmt)
        self.pop_scope()

    def _analyze_statement(self, stmt: _Statement):
        if isinstance(stmt, VarStmt):
            value_type = self._analyze_expression(stmt.expr)
            if not self.scope.define(LocalSymbol(name=stmt.local, type=value_type)):
                self._error(f"Variable '{stmt.local}' is already defined in this scope", stmt)

        if isinstance(stmt, ExprStmt):
            expr_type = self._analyze_expression(stmt.expr)
            if isinstance(expr_type, FunctionType):
                self._error("Expression statement cannot be a function call without parentheses", stmt)

        if isinstance(stmt, AssignStmt):
            assignee_type = self._analyze_expression(stmt.assignee)
            value_type = self._analyze_expression(stmt.value)
            if assignee_type is None or value_type is None:
                return
            if not is_assignable_to(value_type, assignee_type):
                self._error(f"Type mismatch in assignment: cannot assign {value_type} to {assignee_type}", stmt)

        if isinstance(stmt, IfStmt):
            condition_type = self._analyze_expression(stmt.condition)
            if condition_type is not None and not isinstance(condition_type, BoolType):
                self._error(f"If condition must be of type Bool, got {condition_type}", stmt)
            self._analyze_block(stmt.block)
            if stmt.else_block is not None:
                self._analyze_block(stmt.else_block)

    def _analyze_expression(self, expr: _Expression) -> Optional[Type]:
        expr.type = self._resolve_expression_type(expr)
        return expr.type

    def _resolve_expression_type(self, expr: _Expression) -> Optional[Type]:
        if isinstance(expr, BoolExpr):
            return BoolType()

        if isinstance(expr, IntExpr):
            return IntType()

        if isinstance(expr, StringExpr):
            return ObjectType(cls=StandardTypes.STRING_CLASS)

        if isinstance(expr, SymbolExpr):
            symbol = self.scope.lookup(expr.name)
            expr.symbol = symbol
            if symbol is None:
                self._error(f"Undefined symbol {expr.name}", expr)
                return None
            if isinstance(symbol, LocalSymbol):
                return symbol.type
            if isinstance(symbol, ParameterSymbol):
                return symbol.type
            if isinstance(symbol, PropertySymbol):
                return symbol.type
            if isinstance(symbol, FunctionSymbol):
                return symbol.function_type()
            if isinstance(symbol, Class):
                # TODO: Static access (and reflection one day)
                self._error(f"{expr.name} is a type name, not a value", expr)
                return None
            self._error(f"{expr.name} cannot be used as an expression", expr)
            return None

        if isinstance(expr, MemberExpr):
            target_type = self._analyze_expression(expr.expr)
            if target_type is None:
                return None

            if isinstance(target_type, ObjectType):
                member_symbol = target_type.cls.lookup_member(expr.member)
                expr.symbol = member_symbol
                if member_symbol is not None:
                    if isinstance(member_symbol, PropertySymbol):
                        return member_symbol.type
                    if isinstance(member_symbol, FunctionSymbol):
                        return member_symbol.function_type()

                if target_type.cls == StandardTypes.OBJECT_CLASS:
                    # Just like Objective-C >:)
                    self._warning(f"Accessing unknown method {expr.member} on Object, assuming it returns Object", expr)
                    return FunctionType(param_types=None, return_type=ObjectType(cls=StandardTypes.OBJECT_CLASS))

                self._error(f"Undefined member {expr.member} on class {target_type.cls.name}", expr)
                return None

            self._error(f"Member access not supported on type {target_type}", expr)
            return None

        if isinstance(expr, CallExpr):
            callee_type = self._analyze_expression(expr.callee)

            arg_types = []
            for arg in expr.args:
                arg_type = self._analyze_expression(arg)
                arg_types.append(arg_type)

            if callee_type is None:
                # Analyze the arguments to report any errors in them, but don't complain about invalid callee
                return None

            if isinstance(callee_type, FunctionType):
                # If param_types is None, it means we don't know what the function accepts
                if callee_type.param_types is not None:
                    if len(arg_types) != len(callee_type.param_types):
                        self._error(f"Function expects {len(callee_type.param_types)} argument(s), but {len(arg_types)} were provided", expr)
                    else:
                        for i, (arg_type, param_type) in enumerate(zip(arg_types, callee_type.param_types)):
                            if arg_type is not None and not is_assignable_to(arg_type, param_type):
                                self._error(f"Argument {i + 1} type mismatch: expected {param_type}, got {arg_type}", expr)

                return callee_type.return_type

            self._error(f"Attempting to call non-callable type {callee_type}", expr)
            return None

        if isinstance(expr, BinaryExpr):
            lhs_type = self._analyze_expression(expr.lhs)
            rhs_type = self._analyze_expression(expr.rhs)

            if lhs_type is None or rhs_type is None:
                return None

            if type(lhs_type) != type(rhs_type):
                self._error(f"Type mismatch in binary expression: {lhs_type} and {rhs_type}", expr)
                return None

            match expr.op:
                case BinaryOperation.ADD | BinaryOperation.SUB | BinaryOperation.MUL | BinaryOperation.DIV | BinaryOperation.MOD:
                    if isinstance(lhs_type, IntType):
                        return IntType()
                    else:
                        self._error(f"Arithmetic operations only supported on Int, got {lhs_type}", expr)
                        return None
                case BinaryOperation.EQ | BinaryOperation.NEQ | BinaryOperation.GT | BinaryOperation.GTE | BinaryOperation.LT | BinaryOperation.LTE:
                    if isinstance(lhs_type, IntType):
                        return BoolType()
                    else:
                        self._error(f"Comparison operations only supported on Int, got {lhs_type}", expr)
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
