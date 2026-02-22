import sys
from typing import Optional, NoReturn

from compiler.IR import IRFunction, IRInstruction, IRReturn, IROperand
from compiler.symbols import FunctionSymbol
from lang_ast import _Statement, ReturnStmt, _Expression, BoolExpr, IntExpr, StringExpr


def fatal_error(msg: str) -> NoReturn:
    sys.exit(f"internal error: {msg}\nThis is a bug in the compiler, semantic analysis should've caught this!")


class _FunctionCtx:
    pass


class IRLowerer:
    def __init__(self):
        self._function_ctx: Optional[_FunctionCtx] = None
        self._current_block: Optional[list[IRInstruction]] = []

    def _emit(self, i: IRInstruction):
        self._current_block.append(i)

    def _lower_function(self, func: FunctionSymbol) -> IRFunction:
        ir_func = IRFunction(func)
        self._current_block = ir_func.body
        self._lower_block(func.node.block)
        self._current_block = None
        return ir_func

    # Returns True if the block has a return statement
    def _lower_block(self, stmts: list[_Statement]) -> bool:
        for stmt in stmts:
            if isinstance(stmt, ReturnStmt):
                self._emit(IRReturn(self._lower_expr(stmt.expr) if stmt.expr is not None else None))
                return True
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

        print(f"Expression '{expr}' is unknown")
        return "ERROR"
