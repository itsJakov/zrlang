import sys
from typing import Optional, NoReturn

from compiler.IR import IRFunction, IRInstruction, IRReturn, IROperand, IRReg, IRFuncCall, IRVirtualCall, IRStore, \
    IRLoad
from compiler.symbols import FunctionSymbol, ParameterSymbol, Class, MethodSymbol, LocalSymbol
from compiler.types import VoidType
from lang_ast import _Statement, ReturnStmt, _Expression, BoolExpr, IntExpr, StringExpr, ExprStmt, CallExpr, SymbolExpr, \
    MemberExpr, VarStmt


def fatal_error(msg: str) -> NoReturn:
    sys.exit(f"internal error: {msg}\nThis is a bug in the compiler, semantic analysis should've caught this!")


class _FunctionCtx:
    def __init__(self):
        # self._live_locals: set[LocalSymbol] = set()
        self._temp_idx: int = -1

    def temp_teg(self) -> IRReg:
        self._temp_idx += 1
        return IRReg(idx=self._temp_idx)


class IRLowerer:
    def __init__(self):
        self._function_ctx: Optional[_FunctionCtx] = None
        self._current_block: Optional[list[IRInstruction]] = []

    def _emit(self, i: IRInstruction):
        self._current_block.append(i)

    def _lower_function(self, func: FunctionSymbol) -> IRFunction:
        ir_func = IRFunction(func)
        self._function_ctx = _FunctionCtx()
        self._current_block = ir_func.body
        self._lower_block(func.node.block)
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
                self._emit(IRStore(
                    destination=stmt.local,
                    value=self._lower_expr(stmt.expr)
                ))

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
            temp = self._function_ctx.temp_teg()
            self._emit(IRLoad(source=symbol, destination=temp))
            return temp

        if isinstance(expr, CallExpr):
            return self._lower_call_expr(expr)

        print(f"Expression '{expr}' is unknown")
        return "ERROR"

    def _lower_call_expr(self, call: CallExpr) -> IROperand:
        args = [self._lower_expr(arg) for arg in call.args]

        callee = call.callee
        if isinstance(callee, SymbolExpr):
            # Function Call
            if not isinstance(callee.symbol, FunctionSymbol):
                fatal_error(f"Expected a function symbol for call expression")

            destination = self._function_ctx.temp_teg() if callee.symbol.return_type != VoidType() else None
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

            if isinstance(callee.member, (SymbolExpr, ParameterSymbol)) and callee.member.name == "super":
                # Super method call
                pass
            elif isinstance(callee.target, SymbolExpr) and isinstance(callee.target.symbol, Class):
                # Static method call
                pass
            else:
                # Instance method call
                destination = self._function_ctx.temp_teg() if callee.symbol.return_type != VoidType() else None
                self._emit(IRVirtualCall(
                    method=method,
                    target=self._lower_expr(callee.target),
                    args=args,
                    destination=destination
                ))
                return destination

        fatal_error(f"Unknown call expression type '{type(call)}'")
