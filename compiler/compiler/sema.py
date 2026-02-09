import sys
from dataclasses import dataclass, field
from typing import Optional, ContextManager, Union

from lang_ast import ClassDecl, ClassField, MethodDecl, _Expression, IntExpr, StringExpr, SymbolExpr, MemberExpr, \
    CallExpr, BinaryExpr, BinaryOperation, _Statement, VarStmt, ExprStmt, AssignStmt, IfStmt, AllocExpr


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

@dataclass
class Void:
    pass

@dataclass
class Boolean:
    pass

@dataclass
class Integer:
    pass

@dataclass
class String:
    pass

@dataclass
class Instance:
    cls: 'ClassSymbol'

@dataclass
class Symbol:
    name: str

# TODO: Why does a Method have a name? Shouldn't it just be a type?
@dataclass
class Method(Symbol):
    return_type: 'Type'

@dataclass
class ClassSymbol(Symbol):
    methods: dict[str, Method] = field(default_factory=dict)
    fields: dict[str, 'Type'] = field(default_factory=dict)

@dataclass
class LocalSymbol(Symbol):
    type: 'Type'

Type = Union[Void, Boolean, Integer, String, Instance, Method, ClassSymbol]

class StandardSymbols:
    STRING = ClassSymbol(name="String", methods={
        "printToStdout": Method(name="printToStdout", return_type=Void()),
    })
    OBJECT = ClassSymbol(name="RootObject", methods={
        "toString": Method(name="toString", return_type=Instance(cls=STRING)),
    })
    ARRAY = ClassSymbol(name="Array", methods={
        "append": Method(name="append", return_type=Void()),
        "get": Method(name="get", return_type=Instance(cls=OBJECT)),
        "getIsEmpty": Method(name="getIsEmpty", return_type=Boolean())
    })
    PRINT = Method(name="print", return_type=Void())

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
        scope.define(StandardSymbols.STRING) # TODO: Not like this
        scope.define(StandardSymbols.ARRAY)
        scope.define(StandardSymbols.PRINT)
        return scope


class SemanticAnalyzer:
    def __init__(self):
        self.scope = Scope.global_scope()

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
        for cls in ast:
            self._collect_class_info(cls)

        # Pass 2: Verify class hierarchies

        # Pass 3: Verify methods
        for cls in ast:
            for member in cls.members:
                if isinstance(member, MethodDecl):
                    self._analyze_method(member)

        return True

    def _collect_class_info(self, cls: ClassDecl):
        class_info = ClassSymbol(name=cls.name)
        for member in cls.members:
            if isinstance(member, ClassField):
                if member.type == "String":
                    cls = StandardSymbols.STRING
                else:
                    cls = ClassSymbol(name=member.type) # TODO: Resolve Type properly
                class_info.fields[member.name] = Instance(cls=cls)
            elif isinstance(member, MethodDecl):
                class_info.methods[member.name] = Method(name=member.name, return_type=Void())
            else:
                self._error(f"Unknown class member type: {type(member)}")
        self.scope.define(class_info)

    def _analyze_method(self, method: MethodDecl):
        self.push_scope()
        # TODO: Add parameters to scope
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
            self.scope.define(LocalSymbol(name=stmt.local, type=value_type))

        if isinstance(stmt, ExprStmt):
            self._analyze_expression(stmt.expr)

        if isinstance(stmt, AssignStmt):
            assignee_type = self._analyze_expression(stmt.assignee)
            value_type = self._analyze_expression(stmt.value)
            if assignee_type != value_type:
                eprint(f"Type mismatch in assignment: {type(assignee_type).__name__} and {type(value_type).__name__}")

        if isinstance(stmt, IfStmt):
            condition_type = self._analyze_expression(stmt.condition)
            if not isinstance(condition_type, Boolean):
                eprint(f"If condition must be of type Bool, got {type(condition_type).__name__}")
            self._analyze_block(stmt.block)
            if stmt.else_block is not None:
                self._analyze_block(stmt.else_block)


    def _analyze_expression(self, expr: _Expression) -> Optional[Type]:
        if isinstance(expr, IntExpr):
            return Integer()

        if isinstance(expr, StringExpr):
            return Instance(cls=StandardSymbols.STRING)

        # TODO: This is not a good idea what about type names?
        if isinstance(expr, SymbolExpr):
            symbol = self.scope.lookup(expr.name)
            if symbol is None:
                eprint(f"Undefined symbol {expr.name}")
                return None
            if isinstance(symbol, LocalSymbol):
                return symbol.type
            if isinstance(symbol, Method):
                return symbol
            else:
                eprint(f"{expr.name} is not a expression")
                return None

        if isinstance(expr, MemberExpr):
            target_type = self._analyze_expression(expr.expr)
            match target_type:
                case Instance(cls):
                    field_type = cls.fields.get(expr.member)
                    if field_type is not None:
                        return field_type

                    method = cls.methods.get(expr.member)
                    if method is not None:
                        return method

                    # If Field -> return type of the field
                    # If Method -> return Method
                    eprint(f"Undefined member {expr.member} on class {cls.name}")
                    return None
                case ClassSymbol():
                    eprint(f"Static member access not supported yet!")
                    return None
                case _:
                    eprint(f"Member access not supported on type {type(target_type).__name__}")
                    return None

        if isinstance(expr, CallExpr):
            callee_type = self._analyze_expression(expr.callee)
            match callee_type:
                case Method(name, return_type):
                    return return_type
                case _:
                    eprint(f"Attempting to call non-callable type {type(callee_type).__name__}")
                    return None

        if isinstance(expr, BinaryExpr):
            lhs_type = self._analyze_expression(expr.lhs)
            rhs_type = self._analyze_expression(expr.rhs)

            if type(lhs_type) != type(rhs_type):
                eprint(f"Type mismatch in binary expression: {type(lhs_type).__name__} and {type(rhs_type).__name__}")
                return None

            match expr.op:
                case BinaryOperation.ADD | BinaryOperation.SUB | BinaryOperation.MUL | BinaryOperation.DIV:
                    if isinstance(lhs_type, Integer):
                        return Integer()
                    else:
                        eprint(f"Arithmetic operations only supported on Int, got {type(lhs_type).__name__}")
                        return None
                case BinaryOperation.EQ | BinaryOperation.NEQ | BinaryOperation.GT | BinaryOperation.GTE | BinaryOperation.LT | BinaryOperation.LTE:
                    if isinstance(lhs_type, Integer):
                        return Boolean()
                    else:
                        eprint(f"Comparison operations only supported on Int, got {type(lhs_type).__name__}")
                        return None
                case BinaryOperation.AND | BinaryOperation.OR:
                    eprint(f"Logical operators not supported yet!")
                    return None

        if isinstance(expr, AllocExpr):
            class_symbol = self.scope.lookup(expr.cls_name)
            if class_symbol is None:
                eprint(f"Undefined class {expr.cls_name}")
                return None
            if not isinstance(class_symbol, ClassSymbol):
                eprint(f"{expr.cls_name} is not a class")
                return None
            return Instance(cls=class_symbol)

        eprint(f"Unknown expression type: {type(expr).__name__}")
        return None

    def _error(self, message: str):
        eprint(f"Semantic error: {message}")