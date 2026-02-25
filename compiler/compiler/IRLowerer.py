import sys
from typing import Optional, NoReturn

from compiler.IR import IRFunction, IRInstruction, IRReturn, IROperand, IRReg, IRFuncCall, IRVirtualCall, IRStore, \
    IRLoad, IRAlloc, IRStoreField, IRClass, IRMethod, IRSuperCall, IRStaticCall, IRSelf, IRLoadField, IRBinaryOp
from compiler.symbols import FunctionSymbol, ParameterSymbol, Class, MethodSymbol, LocalSymbol, FieldSymbol
from compiler.types import VoidType, Type
from lang_ast import _Statement, ReturnStmt, _Expression, BoolExpr, IntExpr, StringExpr, ExprStmt, CallExpr, SymbolExpr, \
    MemberExpr, VarStmt, AllocExpr, AssignStmt, BinaryExpr


def fatal_error(msg: str) -> NoReturn:
    sys.exit(f"internal error: {msg}\nThis is a bug in the compiler, semantic analysis should've caught this!")


class _FunctionCtx:
    def __init__(self):
        # self._live_locals: set[LocalSymbol] = set()
        self._temp_idx: int = -1

    def temp_teg(self, t: Type) -> IRReg:
        self._temp_idx += 1
        return IRReg(idx=self._temp_idx, type=t)


class IRLowerer:
    def __init__(self):
        # TODO: ugly
        self._function_ctx: Optional[_FunctionCtx] = None
        self._current_func: Optional[IRFunction] = None
        self._current_block: Optional[list[IRInstruction]] = []
        self._current_cls: Optional[Class] = None

    def lower(self, funcs: list[FunctionSymbol], classes: list[Class]) -> tuple[list[IRFunction], list[IRClass]]:
        ir_funcs = [self._lower_function(func) for func in funcs]
        ir_classes = [self._lower_class(cls) for cls in classes]
        return ir_funcs, ir_classes

    def _emit(self, i: IRInstruction):
        self._current_block.append(i)

    def _lower_class(self, cls: Class) -> IRClass:
        self._current_cls = cls
        ir_cls = IRClass(
            sym=cls,
            methods=[self._lower_function(method) for method in cls.members.values() if isinstance(method, MethodSymbol)]
        )
        self._current_cls = None
        return ir_cls

    def _lower_function(self, func: FunctionSymbol) -> IRFunction | IRMethod:
        ir_func = IRFunction(func)
        self._current_func = ir_func
        self._function_ctx = _FunctionCtx()
        self._current_block = ir_func.body
        returns = self._lower_block(func.node.block)
        if not returns:
            self._emit(IRReturn(value=None))
        self._function_ctx = None
        self._function_ctx = None
        self._current_block = None
        return ir_func

    # Returns True if the block has a return statement
    def _lower_block(self, stmts: list[_Statement]) -> bool:
        for stmt in stmts:
            if isinstance(stmt, ReturnStmt):
                self._emit(IRReturn(self._lower_expr(stmt.expr) if stmt.expr is not None else None))
                return True

            elif isinstance(stmt, VarStmt):
                self._current_func.locals.append(stmt.local)
                self._emit(IRStore(
                    destination=stmt.local,
                    value=self._lower_expr(stmt.expr)
                ))

            elif isinstance(stmt, AssignStmt):
                value = self._lower_expr(stmt.value)

                if isinstance(stmt.assignee, (SymbolExpr, MemberExpr)):
                    assignee_symbol = stmt.assignee.symbol
                    if isinstance(assignee_symbol, (LocalSymbol, ParameterSymbol)):
                        self._emit(IRStore(
                            destination=assignee_symbol,
                            value=value
                        ))
                    elif isinstance(assignee_symbol, FieldSymbol):
                        if not isinstance(stmt.assignee, MemberExpr):
                            fatal_error("FieldSymbol assignee must be a MemberExpr")

                        instance = self._lower_expr(stmt.assignee.target)
                        self._emit(IRStoreField(
                            value=value,
                            target=instance,
                            field=assignee_symbol
                        ))
                else:
                    fatal_error(f"Not an assignable expr {type(stmt.assignee)}")

            elif isinstance(stmt, ExprStmt):
                self._lower_expr(stmt.expr)

            else:
                print(f"Statement '{stmt}' is unknown")

        return False

    def _lower_expr(self, expr: _Expression) -> IROperand:
        if isinstance(expr, BoolExpr):
            return expr.value

        if isinstance(expr, IntExpr):
            return expr.value

        if isinstance(expr, StringExpr):
            return expr.value

        if isinstance(expr, SymbolExpr):
            symbol = expr.symbol
            if not isinstance(symbol, (ParameterSymbol, LocalSymbol)):
                fatal_error("Symbol expressions have to resolve to parameter or local symbols")

            if expr.name == "self":
                return IRSelf()

            temp = self._function_ctx.temp_teg(expr.type)
            self._emit(IRLoad(source=symbol, destination=temp))
            return temp

        if isinstance(expr, MemberExpr):
            if expr.member == "services":
                pass

            if not isinstance(expr.symbol, FieldSymbol):
                fatal_error(f"Expected a field symbol for member expression")

            target = self._lower_expr(expr.target)
            temp = self._function_ctx.temp_teg(expr.type)
            self._emit(IRLoadField(
                target=target,
                field=expr.symbol,
                destination=temp
            ))
            return temp

        if isinstance(expr, CallExpr):
            return self._lower_call_expr(expr)

        if isinstance(expr, BinaryExpr):
            lhs = self._lower_expr(expr.lhs)
            rhs = self._lower_expr(expr.rhs)

            temp = self._function_ctx.temp_teg(expr.type)
            self._emit(IRBinaryOp(
                op=expr.op,
                lhs=lhs,
                rhs=rhs,
                destination=temp
            ))
            return temp

        if isinstance(expr, AllocExpr):
            temp = self._function_ctx.temp_teg(expr.type)
            self._emit(IRAlloc(
                cls=expr.cls,
                destination=temp
            ))
            return temp

        print(f"Expression '{expr}' is unknown")
        return "ERROR"

    def _lower_call_expr(self, call: CallExpr) -> IROperand:
        args = [self._lower_expr(arg) for arg in call.args]

        callee = call.callee
        if isinstance(callee, SymbolExpr):
            # Function Call
            if not isinstance(callee.symbol, FunctionSymbol):
                fatal_error(f"Expected a function symbol for call expression")

            destination = self._function_ctx.temp_teg(call.type) if callee.symbol.return_type != VoidType() else None
            self._emit(IRFuncCall(
                func=callee.symbol,
                args=args,
                destination=destination
            ))
            return destination

        elif isinstance(callee, MemberExpr):
            method = callee.symbol
            if not isinstance(method, MethodSymbol):
                fatal_error(f"Expected a method symbol for member call expression")

            if isinstance(callee.target, SymbolExpr) and callee.target.name == "super":
                # Super method call
                destination = self._function_ctx.temp_teg(call.type) if method.return_type != VoidType() else None
                self._emit(IRSuperCall(
                    method=method,
                    cls=self._current_cls.parent,
                    args=args,
                    destination=destination
                ))
                return destination
            elif isinstance(callee.target, SymbolExpr) and isinstance(callee.target.symbol, Class):
                # Static method call
                destination = self._function_ctx.temp_teg(call.type) if method.return_type != VoidType() else None
                self._emit(IRStaticCall(
                    cls=callee.target.symbol,
                    method=callee.symbol,
                    args=args,
                    destination=destination
                ))
                return destination
            else:
                # Instance method call
                destination = self._function_ctx.temp_teg(call.type) if callee.symbol.return_type != VoidType() else None
                self._emit(IRVirtualCall(
                    method=method,
                    target=self._lower_expr(callee.target),
                    args=args,
                    destination=destination
                ))
                return destination

        fatal_error(f"Unknown call expression type '{type(call)}'")
