import sys
from typing import Optional, NoReturn

from compiler.IR import IRFunction, IRInstruction, IRReturn, IROperand, IRReg, IRFuncCall, IRVirtualCall, IRStore, \
    IRLoad, IRAlloc, IRStoreField, IRClass, IRMethod, IRSuperCall, IRStaticCall, IRSelf, IRLoadField, IRBinaryOp, \
    IRBranch, IRRelease, IRRetain, IRStringLiteral, IRLoop, IRBreak, IRContinue
from compiler.symbols import FunctionSymbol, ParameterSymbol, Class, MethodSymbol, LocalSymbol, FieldSymbol
from compiler.types import VoidType, Type, ObjectType
from lang_ast import _Statement, ReturnStmt, _Expression, BoolExpr, IntExpr, StringExpr, ExprStmt, CallExpr, SymbolExpr, \
    MemberExpr, VarStmt, AllocExpr, AssignStmt, BinaryExpr, IfStmt, LoopStmt, BreakStmt, ContinueStmt


def fatal_error(msg: str) -> NoReturn:
    sys.exit(f"internal error: {msg}\nThis is a bug in the compiler, semantic analysis should've caught this!")


def _is_object(op: IROperand) -> bool:
    return isinstance(op, IRReg) and isinstance(op.type, ObjectType)


class _Scope:
    def __init__(self, lowerer: 'IRLowerer', parent: Optional['_Scope'], is_loop: bool):
        self._lowerer = lowerer
        self.parent = parent
        self.is_loop = is_loop
        self.body: list[IRInstruction] = []
        self._live_locals: list[LocalSymbol] = []

    def bind_local(self, local: LocalSymbol) -> None:
        if local not in self._live_locals:
            self._live_locals.append(local)

    def emit_releases(self) -> None:
        for local in reversed(self._live_locals):
            if not isinstance(local.type, ObjectType):
                continue

            tmp = self._lowerer._function.temp_reg(local.type)
            self._lowerer._emit(IRLoad(source=local, destination=tmp))
            self._lowerer._emit(IRRelease(tmp))


class _Value:
    """Wrapper for an IROperand with ownership management."""

    def __init__(self, lowerer: 'IRLowerer', operand: IROperand, owned: bool):
        self._lowerer = lowerer
        self.operand = operand
        self.owned = owned

    def take(self) -> IROperand:
        """Claim ownership. Retains if borrowed, transfers if already owned."""
        if not self.owned and _is_object(self.operand):
            self._lowerer._emit(IRRetain(self.operand))

        self.owned = False
        return self.operand

    def discard(self) -> None:
        """Release immediately if owned, no-op if borrowed."""
        if self.owned and _is_object(self.operand):
            self._lowerer._emit(IRRelease(self.operand))

        self.owned = False

    def use(self) -> IROperand:
        return self.operand


class _FunctionCtx:
    def __init__(self, func: IRFunction):
        self.func = func
        self._temp_idx = -1

    def temp_reg(self, t: Type) -> IRReg:
        self._temp_idx += 1
        return IRReg(idx=self._temp_idx, type=t)


class IRLowerer:
    def __init__(self):
        self._scope: Optional[_Scope] = None
        self._function: Optional[_FunctionCtx] = None
        self._current_cls: Optional[Class] = None

    def lower(self, funcs: list[FunctionSymbol], classes: list[Class]) -> tuple[list[IRFunction], list[IRClass]]:
        ir_funcs = [self._lower_function(func) for func in funcs]
        ir_classes = [self._lower_class(cls) for cls in classes]
        return ir_funcs, ir_classes

    # -- Utilities

    def _emit(self, i: IRInstruction) -> None:
        self._scope.body.append(i)

    def _emit_return(self, value: Optional[IROperand]) -> None:
        scope = self._scope
        # Recursively emit releases for scopes all scopes in order
        while scope is not None:
            scope.emit_releases()
            scope = scope.parent

        self._emit(IRReturn(value))

    def _emit_loop_exit(self, terminator: IRContinue | IRBreak) -> None:
        # Recursively emit releases for scopes until the first loop scope is reached
        scope = self._scope
        while scope is not None:
            scope.emit_releases()
            if scope.is_loop:
                self._emit(terminator)
                return # Stop at the first loop scope
            scope = scope.parent

        fatal_error("Loop exit outside of a loop")

    def _owned(self, op: Optional[IROperand]) -> _Value:
        return _Value(self, op, owned=op is not None and _is_object(op))

    def _borrowed(self, op: IROperand) -> _Value:
        return _Value(self, op, owned=False)

    # -- Top-level lowering

    def _lower_class(self, cls: Class) -> IRClass:
        self._current_cls = cls
        ir_cls = IRClass(
            sym=cls,
            methods=[self._lower_function(m) for m in cls.members.values() if isinstance(m, MethodSymbol)],
        )
        self._current_cls = None
        return ir_cls

    def _lower_function(self, func: FunctionSymbol) -> IRFunction | IRMethod:
        ir_func = IRFunction(func)
        self._function = _FunctionCtx(ir_func)
        body, terminated = self._lower_block(func.node.block)
        if not terminated:
            body.append(IRReturn(None)) # Not emit_release because an unterminated block cleaned itself up
        ir_func.body = body
        self._function = None
        return ir_func

    # -- Statements

    def _lower_block(self, stmts: list[_Statement], is_loop: bool = False) -> tuple[list[IRInstruction], bool]:
        """Lower a list of statements into an IR block under a new scope.

        Only fall-through, releases are emitted for the scope's locals.
        If a statement terminates control flow (return, break, continue),
        the terminator already cleaned the scope.

        Returns (body, terminated). The caller decides what, if anything,
        to append to the body when not terminated (implicit return, loop jump, etc).
        """
        self._scope = _Scope(self, parent=self._scope, is_loop=is_loop)
        terminated = False
        for stmt in stmts:
            if self._lower_stmt(stmt):
                terminated = True
                break

        if not terminated:
            self._scope.emit_releases()

        block = self._scope
        self._scope = block.parent
        return block.body, terminated

    def _lower_stmt(self, stmt: _Statement) -> bool:
        if isinstance(stmt, ReturnStmt):
            value = self._lower_expr(stmt.expr).take() if stmt.expr is not None else None
            self._emit_return(value)
            return True

        if isinstance(stmt, VarStmt):
            self._function.func.locals.append(stmt.local)
            new_op = self._lower_expr(stmt.expr).take() # TODO: stmt.expr could be None!
            self._emit(IRStore(destination=stmt.local, value=new_op))
            self._scope.bind_local(stmt.local)
            return False

        if isinstance(stmt, AssignStmt):
            self._lower_assign(stmt)
            return False

        if isinstance(stmt, IfStmt):
            cond = self._lower_expr(stmt.condition)
            true_block, _ = self._lower_block(stmt.block)

            false_block: Optional[list[IRInstruction]] = None
            if stmt.else_block:
                false_block, _ = self._lower_block(stmt.else_block)

            self._emit(IRBranch(condition=cond.use(), true_block=true_block, false_block=false_block))
            cond.discard() # No-op in practice: cond is a primitive (bool).
            return False

        if isinstance(stmt, LoopStmt):
            body, _ = self._lower_block(stmt.block, is_loop=True)
            self._emit(IRLoop(body))
            return False

        if isinstance(stmt, BreakStmt):
            self._emit_loop_exit(IRBreak())
            return True

        if isinstance(stmt, ContinueStmt):
            self._emit_loop_exit(IRContinue())
            return True

        if isinstance(stmt, ExprStmt):
            self._lower_expr(stmt.expr).discard()
            return False

        fatal_error(f"Statement '{stmt}' is unknown")

    def _lower_assign(self, stmt: AssignStmt) -> None:
        if not isinstance(stmt.assignee, (SymbolExpr, MemberExpr)):
            fatal_error(f"Not an assignable expr {type(stmt.assignee)}")

        symbol = stmt.assignee.symbol
        value = self._lower_expr(stmt.value).take()

        if isinstance(symbol, (LocalSymbol, ParameterSymbol)):
            if isinstance(symbol, LocalSymbol):
                # Skip release for ParameterSymbol, the old value is the caller's.
                # TODO: [BUG] ParameterSymbol will leak
                self._release_storage(symbol)
            self._emit(IRStore(destination=symbol, value=value))
            return

        if isinstance(symbol, FieldSymbol):
            if not isinstance(stmt.assignee, MemberExpr):
                fatal_error("FieldSymbol assignee must be a MemberExpr")
            instance = self._lower_expr(stmt.assignee.target)

            # Release old field value
            if isinstance(symbol.type, ObjectType):
                tmp = self._function.temp_reg(symbol.type)
                self._emit(IRLoadField(target=instance.use(), field=symbol, destination=tmp))
                self._emit(IRRelease(tmp))

            self._emit(IRStoreField(value=value, target=instance.use(), field=symbol))
            instance.discard()
            return

        fatal_error(f"Cannot assign to symbol of type {type(symbol)}")

    def _release_storage(self, storage: LocalSymbol | ParameterSymbol) -> None:
        if not isinstance(storage.type, ObjectType):
            return
        tmp = self._function.temp_reg(storage.type)
        self._emit(IRLoad(source=storage, destination=tmp))
        self._emit(IRRelease(tmp))

    # -- Expressions

    def _lower_expr(self, expr: _Expression) -> _Value:
        if isinstance(expr, BoolExpr):
            return self._borrowed(expr.value)
        if isinstance(expr, IntExpr):
            return self._borrowed(expr.value)
        if isinstance(expr, StringExpr):
            dest = self._function.temp_reg(expr.type)
            self._emit(IRStringLiteral(value=expr.value, destination=dest))
            return self._owned(dest)
        if isinstance(expr, SymbolExpr):
            return self._lower_symbol_expr(expr)
        if isinstance(expr, MemberExpr):
            return self._lower_member_expr(expr)
        if isinstance(expr, CallExpr):
            # Functions MUST return owned (+1) values
            return self._owned(self._lower_call_expr(expr))
        if isinstance(expr, BinaryExpr):
            return self._lower_binary_expr(expr)
        if isinstance(expr, AllocExpr):
            dest = self._function.temp_reg(expr.type)
            self._emit(IRAlloc(cls=expr.cls, destination=dest))
            return self._owned(dest)

        fatal_error(f"Expression '{expr}' is unknown")

    def _lower_symbol_expr(self, expr: SymbolExpr) -> _Value:
        symbol = expr.symbol
        if not isinstance(symbol, (ParameterSymbol, LocalSymbol)):
            fatal_error("Symbol expressions have to resolve to parameter or local symbols")
        if expr.name == "self":
            return self._borrowed(IRSelf())
        dest = self._function.temp_reg(expr.type)
        self._emit(IRLoad(source=symbol, destination=dest))
        return self._borrowed(dest)

    def _lower_member_expr(self, expr: MemberExpr) -> _Value:
        if not isinstance(expr.symbol, FieldSymbol):
            fatal_error("Expected a field symbol for member expression")
        target = self._lower_expr(expr.target)
        dest = self._function.temp_reg(expr.type)
        self._emit(IRLoadField(target=target.use(), field=expr.symbol, destination=dest))
        target.discard()
        return self._borrowed(dest)

    def _lower_binary_expr(self, expr: BinaryExpr) -> _Value:
        lhs = self._lower_expr(expr.lhs)
        rhs = self._lower_expr(expr.rhs)
        dest = self._function.temp_reg(expr.type)
        self._emit(IRBinaryOp(op=expr.op, lhs=lhs.use(), rhs=rhs.use(), destination=dest))
        lhs.discard()
        rhs.discard()
        return self._borrowed(dest)  # Binary ops produce primitives only (for now)

    def _lower_call_expr(self, call: CallExpr) -> Optional[IRReg]:
        args = [self._lower_expr(arg) for arg in call.args]
        arg_ops = [arg.use() for arg in args]
        dest = self._emit_call(call, arg_ops)
        for arg in args:
            arg.discard()
        return dest

    def _emit_call(self, call: CallExpr, arg_ops: list[IROperand]) -> Optional[IRReg]:
        return_type = call.type
        dest = self._function.temp_reg(return_type) if return_type != VoidType() else None
        callee = call.callee

        if isinstance(callee, SymbolExpr):
            if not isinstance(callee.symbol, FunctionSymbol):
                fatal_error("Expected a function symbol for call expression")
            self._emit(IRFuncCall(func=callee.symbol, args=arg_ops, destination=dest))
            return dest

        if isinstance(callee, MemberExpr):
            method = callee.symbol
            if not isinstance(method, MethodSymbol):
                fatal_error("Expected a method symbol for member call expression")
            target_expr = callee.target

            if isinstance(target_expr, SymbolExpr) and target_expr.name == "super":
                self._emit(IRSuperCall(
                    cls=self._current_cls.parent, method=method,
                    args=arg_ops, destination=dest,
                ))
                return dest

            if isinstance(target_expr, SymbolExpr) and isinstance(target_expr.symbol, Class):
                self._emit(IRStaticCall(
                    cls=target_expr.symbol, method=method,
                    args=arg_ops, destination=dest,
                ))
                return dest

            target = self._lower_expr(target_expr)
            self._emit(IRVirtualCall(
                method=method, target=target.use(),
                args=arg_ops, destination=dest,
            ))
            target.discard()
            return dest

        fatal_error(f"Unknown call expression type '{type(call)}'")
