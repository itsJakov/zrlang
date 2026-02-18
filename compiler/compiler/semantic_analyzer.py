import sys
from typing import Optional

from lang_ast import (
    ClassDecl, ClassField, FuncDecl, _Expression, IntExpr, StringExpr,
    SymbolExpr, MemberExpr, CallExpr, BinaryExpr, BinaryOperation,
    _Statement, VarStmt, ExprStmt, AssignStmt, IfStmt, AllocExpr,
    _Ast, ReturnStmt, BoolExpr, _TopLevelDecl, FuncDecorator
)
from .types import (
    Type, VoidType, BoolType, IntType, ObjectType, FunctionType,
    is_assignable_to, ClassType
)
from .symbols import (
    LocalSymbol, FieldSymbol, ParameterSymbol,
    FunctionSymbol, Class, MethodSymbol
)
from .scope import Scope
from .standard_types import StandardTypes


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class SemanticAnalyzer:
    def __init__(self, source_name: str = "<input>"):
        self.scope = StandardTypes.create_global_scope()
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

    def _push_scope(self) -> Scope:
        new_scope = Scope(parent=self.scope)
        # TODO: Probably should find a better way to handle return/break/continue scopes
        new_scope.return_type = self.scope.return_type
        self.scope = new_scope
        return new_scope

    def _pop_scope(self):
        if self.scope.parent is not None:
            self.scope = self.scope.parent
        else:
            raise Exception("Cannot pop global scope")

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

    def analyze(self, ast: list[_TopLevelDecl]) -> bool:
        func_decls = [decl for decl in ast if isinstance(decl, FuncDecl)]
        class_decls = [decl for decl in ast if isinstance(decl, ClassDecl)]

        # Pass 1: Collect Class symbols
        for cls_decl in class_decls:
            symbol = Class(name=cls_decl.name)
            cls_decl.cls = symbol
            if not self.scope.define(symbol):
                self._error(f"Symbol '{symbol.name}' is already defined", cls_decl)

        # Pass 2: Resolve class hierarchies
        for decl in ast:
            if isinstance(decl, ClassDecl):
                self._resolve_class_superclass(decl)

        # Functions and methods must be collected after class hierarchies are resolved
        # Because Functions and Methods need to know custom type information (for parameters and return types)
        # i.e. Types are available after pass 2!

        # Pass 3: Collect Class member symbols (fields and methods)
        for cls_decl in class_decls:
            self._collect_class_members(cls_decl)

        # Pass 4: Collect Function symbols
        for func_decl in func_decls:
            symbol = FunctionSymbol(name=func_decl.name, params=[], return_type=VoidType())
            func_decl.sym = symbol
            self._analyze_function_signature(func_decl)
            if not self.scope.define(symbol):
                self._error(f"Symbol '{symbol.name}' is already defined", func_decl)

        # After passes 3 and 4, all function signatures are resolved
        # So now can finally check function bodies with full type information
        # i.e. Functions/Methods are available after pass 4!

        # Pass 5: Verify functions and methods bodies
        for decl in ast:
            if isinstance(decl, FuncDecl):
                self._analyze_function_body(decl)
            elif isinstance(decl, ClassDecl):
                self._analyze_class_method_bodies(decl)

        return self.error_count == 0

    def _resolve_class_superclass(self, cls_decl: ClassDecl):
        """Resolve parent class for a class."""
        cls = cls_decl.cls

        # If no superclass is specified, set parent to Object
        cls.parent = StandardTypes.OBJECT_CLASS
        if cls_decl.super is None:
            return

        parent_sym = self.scope.lookup(cls_decl.super)
        if parent_sym is None:
            self._error(f"Unknown parent class '{cls_decl.super}'", cls_decl)
            return
        if not isinstance(parent_sym, Class):
            self._error(f"'{cls_decl.super}' is not a class", cls_decl)
            return

        cls.parent = parent_sym

    def _analyze_function_signature(self, func_decl: FuncDecl):
        func_sym: FunctionSymbol = func_decl.sym
        func_sym.return_type = self._resolve_type_name(func_decl.return_type_name, func_decl) if func_decl.return_type_name else VoidType()

        for param in func_decl.params:
            param_sym = ParameterSymbol(name=param.name, type=self._resolve_type_name(param.type_name, param))
            param.type = param_sym.type
            func_sym.params.append(param_sym)

    def _collect_class_members(self, cls_decl: ClassDecl):
        for member in cls_decl.members:
            if isinstance(member, ClassField):
                field_type = self._resolve_type_name(member.type, member)
                if not cls_decl.cls.define(FieldSymbol(name=member.name, type=field_type, is_static=False)):
                    self._error(f"Member '{member.name}' is already defined in class '{cls_decl.name}'", member)

            elif isinstance(member, FuncDecl):
                method_symbol = MethodSymbol(
                    name=member.name,
                    is_static=FuncDecorator.STATIC in member.decorators,
                    params=[],
                    return_type=VoidType()
                )
                member.sym = method_symbol
                self._analyze_function_signature(member)

                if not cls_decl.cls.define(method_symbol):
                    self._error(f"Member '{member.name}' is already defined in class '{cls_decl.name}'", member)

            else:
                self._error(f"Unknown class member type: {type(member)}", member)

    def _analyze_function_body(self, func_decl: FuncDecl, self_type: Optional[ObjectType] = None):
        self._push_scope()
        func_sym: FunctionSymbol = func_decl.sym

        if self_type is not None:
            self.scope.define(ParameterSymbol(name="self", type=self_type))
            if self_type.cls.parent is not None:
                self.scope.define(ParameterSymbol(name="super", type=ObjectType(cls=self_type.cls.parent)))

        for param in func_sym.params:
            if not self.scope.define(param):
                self._error(f"Parameter '{param.name}' is already defined", param)
        self.scope.return_type = func_sym.return_type

        self._analyze_block(func_decl.block)
        self._pop_scope()

    def _analyze_class_method_bodies(self, cls_decl: ClassDecl):
        self._check_method_overrides(cls_decl)

        self_type = ObjectType(cls_decl.cls)
        for member in cls_decl.members:
            if isinstance(member, FuncDecl):
                self._analyze_function_body(member, self_type=None if member.sym.is_static else self_type)

    def _check_method_overrides(self, cls_decl: ClassDecl):
        cls = cls_decl.cls
        for member in cls_decl.members:
            if not isinstance(member, FuncDecl):
                continue
            func_decl: FuncDecl = member
            is_override = FuncDecorator.OVERRIDE in func_decl.decorators

            method = cls.lookup_member(member.name)
            if method is None or not isinstance(method, MethodSymbol):
                continue  # Should never happen

            # Error 1: Method has override keyword but does not override any parent method
            parent_method = cls.parent.lookup_member(func_decl.name) if cls.parent else None
            if parent_method is None or not isinstance(parent_method, MethodSymbol):
                if is_override:
                    self._error(
                        f"Method '{func_decl.name}' has 'override' but does not override any parent method",
                        func_decl
                    )
                continue

            # Error 2: Method overrides a method without override keyword
            if not is_override:
                self._error(
                    f"Method '{func_decl.name}' overrides parent method but missing 'override'",
                    func_decl
                )

            # Error 3: Method overrides a static method
            if parent_method.is_static:
                self._error(
                    f"Method '{func_decl.name}' cannot override static method in parent class",
                    func_decl
                )

            # Error 3: Method signature does not match parent method signature
            if len(method.params) != len(parent_method.params):
                self._error(
                    f"Method '{method.name}' has {len(method.params)} parameter(s), "
                    f"but parent method has {len(parent_method.params)}",
                    func_decl
                )
                continue

            # TODO: Should contravariance and covariance be allowed for parameters and return types?

            # Check parameter types (contravariance: parent param type should be assignable to child param type)
            for i, (child_param, parent_param) in enumerate(zip(method.params, parent_method.params)):
                if not is_assignable_to(parent_param.type, child_param.type):
                    self._error(
                        f"Method '{method.name}' parameter {i + 1} type '{child_param.type}' is not compatible "
                        f"with parent parameter type '{parent_param.type}'",
                        func_decl
                    )

            # Check return type (covariance: child return type should be assignable to parent return type)
            if not is_assignable_to(method.return_type, parent_method.return_type):
                self._error(
                    f"Method '{method.name}' return type '{method.return_type}' is not compatible "
                    f"with parent return type '{parent_method.return_type}'",
                    func_decl
                )

    def _analyze_block(self, block: list[_Statement]):
        self._push_scope()
        for stmt in block:
            if isinstance(stmt, ReturnStmt):
                value_type = VoidType()
                if stmt.expr is not None:
                    value_type = self._analyze_expression(stmt.expr)

                if not is_assignable_to(value_type, self.scope.return_type):
                    self._error(
                        f"Return type mismatch: expected {self.scope.return_type}, got {value_type}",
                        stmt
                    )
                continue
            self._analyze_statement(stmt)
        self._pop_scope()

    def _analyze_statement(self, stmt: _Statement):
        if isinstance(stmt, VarStmt):
            value_type = self._analyze_expression(stmt.expr)
            if not self.scope.define(LocalSymbol(name=stmt.local, type=value_type)):
                self._error(f"Variable '{stmt.local}' is already defined in this scope", stmt)

        elif isinstance(stmt, ExprStmt):
            expr_type = self._analyze_expression(stmt.expr)
            if isinstance(expr_type, FunctionType):
                self._error("Expression statement cannot be a function call without parentheses", stmt)

        elif isinstance(stmt, AssignStmt):
            assignee_type = self._analyze_expression(stmt.assignee)
            value_type = self._analyze_expression(stmt.value)
            if assignee_type is None or value_type is None:
                return

            if isinstance(stmt.assignee, SymbolExpr) and (stmt.assignee.name == "self" or stmt.assignee.name == "super"):
                self._error("Cannot assign to 'self'", stmt)
                return

            if not is_assignable_to(value_type, assignee_type):
                self._error(
                    f"Type mismatch in assignment: cannot assign {value_type} to {assignee_type}",
                    stmt
                )

        elif isinstance(stmt, IfStmt):
            condition_type = self._analyze_expression(stmt.condition)
            if condition_type is not None and not isinstance(condition_type, BoolType):
                self._error(f"If condition must be of type Bool, got {condition_type}", stmt)

            self._analyze_block(stmt.block)
            if stmt.else_block is not None:
                self._analyze_block(stmt.else_block)

    def _analyze_expression(self, expr: _Expression, allow_class_type: bool = False) -> Optional[Type]:
        # allow_class_type is used for static member, because usually it's not a valid type
        expr.type = self._resolve_expression_type(expr)
        if not allow_class_type and isinstance(expr.type, ClassType):
            self._error(f"Class types cannot be used as expressions", expr)
            return None
        return expr.type

    def _resolve_expression_type(self, expr: _Expression) -> Optional[Type]:
        if isinstance(expr, BoolExpr):
            return BoolType()

        if isinstance(expr, IntExpr):
            return IntType()

        if isinstance(expr, StringExpr):
            return ObjectType(cls=StandardTypes.STRING_CLASS)

        if isinstance(expr, SymbolExpr):
            return self._resolve_symbol_expr(expr)

        if isinstance(expr, MemberExpr):
            return self._resolve_member_expr(expr)

        if isinstance(expr, CallExpr):
            return self._resolve_call_expr(expr)

        if isinstance(expr, BinaryExpr):
            return self._resolve_binary_expr(expr)

        if isinstance(expr, AllocExpr):
            return self._resolve_alloc_expr(expr)

        self._error(f"Unknown expression type: {type(expr).__name__}", expr)
        return None

    def _resolve_symbol_expr(self, expr: SymbolExpr) -> Optional[Type]:
        symbol = self.scope.lookup(expr.name)
        expr.symbol = symbol
        if symbol is None:
            self._error(f"Undefined symbol {expr.name}", expr)
            return None
        if isinstance(symbol, LocalSymbol):
            return symbol.type
        if isinstance(symbol, ParameterSymbol):
            return symbol.type
        if isinstance(symbol, FieldSymbol):
            return symbol.type
        if isinstance(symbol, FunctionSymbol):
            return symbol.function_type()
        if isinstance(symbol, Class):
            return ClassType(symbol)
        self._error(f"{expr.name} cannot be used as an expression", expr)
        return None

    def _resolve_member_expr(self, expr: MemberExpr) -> Optional[Type]:
        target_type = self._analyze_expression(expr.target, allow_class_type=True)
        if target_type is None:
            return None

        if isinstance(target_type, ClassType):
            member_symbol = target_type.cls.lookup_member(expr.member)
            expr.symbol = member_symbol
            if member_symbol is not None:
                if not member_symbol.is_static:
                    self._error(f"Cannot access non-static member '{expr.member}' on class '{target_type.cls.name}'", expr)
                    return None

                if isinstance(member_symbol, FieldSymbol):
                    return member_symbol.type
                if isinstance(member_symbol, MethodSymbol):
                    return member_symbol.function_type()

            self._error(f"Undefined static member {expr.member} on class {target_type.cls.name}", expr)
            return None

        if isinstance(target_type, ObjectType):
            member_symbol = target_type.cls.lookup_member(expr.member)
            expr.symbol = member_symbol
            if member_symbol is not None:
                if member_symbol.is_static:
                    self._error(f"Cannot access static member '{expr.member}' on instance of '{target_type.cls.name}'", expr)
                    return None

                if isinstance(member_symbol, FieldSymbol):
                    return member_symbol.type
                if isinstance(member_symbol, MethodSymbol):
                    return member_symbol.function_type()

            if target_type.cls == StandardTypes.OBJECT_CLASS:
                # Just like Objective-C >:)
                self._warning(
                    f"Accessing unknown method {expr.member} on Object, assuming it returns Object",
                    expr
                )
                return FunctionType(
                    param_types=None,
                    return_type=ObjectType(StandardTypes.OBJECT_CLASS)
                )

            self._error(f"Undefined member {expr.member} on class {target_type.cls.name}", expr)
            return None

        self._error(f"Member access not supported on type {target_type}", expr)
        return None

    def _resolve_call_expr(self, expr: CallExpr) -> Optional[Type]:
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
                    self._error(
                        f"Function expects {len(callee_type.param_types)} argument(s), "
                        f"but {len(arg_types)} were provided",
                        expr
                    )
                else:
                    for i, (arg_type, param_type) in enumerate(zip(arg_types, callee_type.param_types)):
                        if arg_type is not None and not is_assignable_to(arg_type, param_type):
                            self._error(
                                f"Argument {i + 1} type mismatch: expected {param_type}, got {arg_type}",
                                expr
                            )

            return callee_type.return_type

        self._error(f"Attempting to call non-callable type {callee_type}", expr)
        return None

    def _resolve_binary_expr(self, expr: BinaryExpr) -> Optional[Type]:
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
                self._error("Logical operators not supported yet!", expr)
                return None

    def _resolve_alloc_expr(self, expr: AllocExpr) -> Optional[Type]:
        class_symbol = self.scope.lookup(expr.cls_name)
        if class_symbol is None:
            self._error(f"Undefined class {expr.cls_name}", expr)
            return None
        if not isinstance(class_symbol, Class):
            self._error(f"{expr.cls_name} is not a class", expr)
            return None
        return ObjectType(cls=class_symbol)