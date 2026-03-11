import sys
from typing import Optional, NoReturn

from compiler.IR import IRFunction, IRInstruction, IRReturn, IROperand, IRReg, IRFuncCall, IRVirtualCall, IRStore, \
    IRLoad, IRAlloc, IRStoreField, IRClass, IRMethod, IRSuperCall, IRStaticCall, IRSelf, IRLoadField, IRBinaryOp, \
    IRBranch, IRRelease, IRRetain
from compiler.symbols import FunctionSymbol, ParameterSymbol, Class, MethodSymbol, LocalSymbol, FieldSymbol
from compiler.types import VoidType, Type, ObjectType
from lang_ast import _Statement, ReturnStmt, _Expression, BoolExpr, IntExpr, StringExpr, ExprStmt, CallExpr, SymbolExpr, \
    MemberExpr, VarStmt, AllocExpr, AssignStmt, BinaryExpr, IfStmt


def fatal_error(msg: str) -> NoReturn:
    sys.exit(f"internal error: {msg}\nThis is a bug in the compiler, semantic analysis should've caught this!")


class _FunctionCtx:
    def __init__(self, func: IRFunction):
        self.func: IRFunction = func
        self._temp_idx: int = -1

    def temp_reg(self, t: Type) -> IRReg:
        self._temp_idx += 1
        return IRReg(idx=self._temp_idx, type=t)


class _BlockCtx:
    def __init__(self, parent: Optional['_BlockCtx'] = None):
        self.parent: Optional['_BlockCtx'] = parent
        self.block: list[IRInstruction] = []
        self.live_locals: set[LocalSymbol] = set()


class IRLowerer:
    def __init__(self):
        # TODO: ugly
        self._block_ctx: Optional[_BlockCtx] = None
        self._function_ctx: Optional[_FunctionCtx] = None
        self._current_cls: Optional[Class] = None

    def lower(self, funcs: list[FunctionSymbol], classes: list[Class]) -> tuple[list[IRFunction], list[IRClass]]:
        ir_funcs = [self._lower_function(func) for func in funcs]
        ir_classes = [self._lower_class(cls) for cls in classes]
        return ir_funcs, ir_classes

    def _push_block(self):
        self._block_ctx = _BlockCtx(parent=self._block_ctx)

    def _pop_block(self):
        for local in self._block_ctx.live_locals:
            pass

        self._block_ctx = self._block_ctx.parent

    def _emit(self, i: IRInstruction):
        self._block_ctx.block.append(i)

    # Emits a release if needed (register with an object type)
    def _retain(self, operand: IROperand):
        if isinstance(operand, IRReg) and isinstance(operand.type, ObjectType):
            self._emit(IRRetain(operand))

    # Same as _retain but for releases
    def _release(self, operand: IROperand):
        if isinstance(operand, IRReg) and isinstance(operand.type, ObjectType):
            self._emit(IRRelease(operand))

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
        self._function_ctx = _FunctionCtx(ir_func)

        self._push_block()
        returns = self._lower_block(func.node.block)
        if not returns:
            self._emit(IRReturn(value=None))
        ir_func.body = self._block_ctx.block
        self._pop_block()

        self._function_ctx = None
        return ir_func

    # Returns True if the block has a return statement
    def _lower_block(self, stmts: list[_Statement]) -> bool:
        for stmt in stmts:
            if isinstance(stmt, ReturnStmt):
                if stmt.expr is None:
                    self._emit(IRReturn(None))
                else:
                    value, owned = self._lower_expr(stmt.expr)
                    if not owned:
                        self._retain(value)
                    # TODO: Release live locals here
                    self._emit(IRReturn(value))
                return True

            elif isinstance(stmt, VarStmt):
                self._function_ctx.func.locals.append(stmt.local)
                self._block_ctx.live_locals.add(stmt.local)
                self._emit(IRStore(
                    destination=stmt.local,
                    value=self._lower_expr(stmt.expr)[0] # TODO: Handle ARC
                ))

            elif isinstance(stmt, AssignStmt):
                value = self._lower_expr(stmt.value)

                if isinstance(stmt.assignee, (SymbolExpr, MemberExpr)):
                    assignee_symbol = stmt.assignee.symbol
                    if isinstance(assignee_symbol, (LocalSymbol, ParameterSymbol)):
                        if isinstance(assignee_symbol, LocalSymbol):
                            self._block_ctx.live_locals.add(assignee_symbol)

                        self._emit(IRStore(
                            destination=assignee_symbol,
                            value=value[0] # TODO: Handle ARC
                        ))
                    elif isinstance(assignee_symbol, FieldSymbol):
                        if not isinstance(stmt.assignee, MemberExpr):
                            fatal_error("FieldSymbol assignee must be a MemberExpr")

                        instance, owned = self._lower_expr(stmt.assignee.target)
                        self._emit(IRStoreField(
                            value=value[0], # TOOD: Handle ARC
                            target=instance,
                            field=assignee_symbol
                        ))
                        if owned:
                            self._release(instance)
                else:
                    fatal_error(f"Not an assignable expr {type(stmt.assignee)}")

            elif isinstance(stmt, IfStmt):
                condition, owned = self._lower_expr(stmt.condition)

                self._push_block()
                self._lower_block(stmt.block)
                true_block = self._block_ctx.block
                self._pop_block()

                false_block: Optional[list[IRInstruction]] = None
                if stmt.else_block:
                    self._push_block()
                    self._lower_block(stmt.else_block)
                    false_block = self._block_ctx.block
                    self._pop_block()

                self._emit(IRBranch(
                    condition=condition,
                    true_block=true_block,
                    false_block=false_block
                ))

                if owned:
                    self._release(condition)

            elif isinstance(stmt, ExprStmt):
                value, owned = self._lower_expr(stmt.expr)
                if owned:
                    self._release(value)

            else:
                print(f"Statement '{stmt}' is unknown")

        return False

    # bool contains ownership
    # true -> +1 retain count, caller has to release
    # false -> +0 retain count, caller does not have to release or retain if needed
    def _lower_expr(self, expr: _Expression) -> tuple[IROperand, bool]:
        if isinstance(expr, BoolExpr):
            return expr.value, False

        if isinstance(expr, IntExpr):
            return expr.value, False

        if isinstance(expr, StringExpr):
            return expr.value, False

        if isinstance(expr, SymbolExpr):
            symbol = expr.symbol
            if not isinstance(symbol, (ParameterSymbol, LocalSymbol)):
                fatal_error("Symbol expressions have to resolve to parameter or local symbols")

            if expr.name == "self":
                return IRSelf(), False

            temp = self._function_ctx.temp_reg(expr.type)
            self._emit(IRLoad(source=symbol, destination=temp))
            return temp, False

        if isinstance(expr, MemberExpr):
            if not isinstance(expr.symbol, FieldSymbol):
                fatal_error(f"Expected a field symbol for member expression")

            target, owned = self._lower_expr(expr.target)
            temp = self._function_ctx.temp_reg(expr.type)
            self._emit(IRLoadField(
                target=target,
                field=expr.symbol,
                destination=temp
            ))
            if owned:
                self._release(target)
            return temp, False

        if isinstance(expr, CallExpr):
            return self._lower_call_expr(expr), True # Calls always result in +1

        if isinstance(expr, BinaryExpr):
            lhs, lhs_owned = self._lower_expr(expr.lhs)
            rhs, rhs_owned = self._lower_expr(expr.rhs)

            temp = self._function_ctx.temp_reg(expr.type)
            self._emit(IRBinaryOp(
                op=expr.op,
                lhs=lhs,
                rhs=rhs,
                destination=temp
            ))

            if lhs_owned:
                self._release(lhs)
            if rhs_owned:
                self._release(rhs)

            return temp, False # Binary operations can only return ints and bools (for now)

        if isinstance(expr, AllocExpr):
            temp = self._function_ctx.temp_reg(expr.type)
            self._emit(IRAlloc(
                cls=expr.cls,
                destination=temp
            ))
            return temp, True

        print(f"Expression '{expr}' is unknown")
        return "ERROR", False

    def _lower_call_expr(self, call: CallExpr) -> IROperand:
        args = [self._lower_expr(arg) for arg in call.args]
        arg_ops = [arg[0] for arg in args]

        def release_args():
            for arg, owned in args:
                if owned:
                    self._release(arg)

        callee = call.callee
        if isinstance(callee, SymbolExpr):
            # Function Call
            if not isinstance(callee.symbol, FunctionSymbol):
                fatal_error(f"Expected a function symbol for call expression")

            destination = self._function_ctx.temp_reg(call.type) if callee.symbol.return_type != VoidType() else None
            self._emit(IRFuncCall(
                func=callee.symbol,
                args=arg_ops,
                destination=destination
            ))
            release_args()
            return destination

        elif isinstance(callee, MemberExpr):
            method = callee.symbol
            if not isinstance(method, MethodSymbol):
                fatal_error(f"Expected a method symbol for member call expression")

            if isinstance(callee.target, SymbolExpr) and callee.target.name == "super":
                # Super method call
                destination = self._function_ctx.temp_reg(call.type) if method.return_type != VoidType() else None
                self._emit(IRSuperCall(
                    method=method,
                    cls=self._current_cls.parent,
                    args=arg_ops,
                    destination=destination
                ))
                release_args()
                return destination
            elif isinstance(callee.target, SymbolExpr) and isinstance(callee.target.symbol, Class):
                # Static method call
                destination = self._function_ctx.temp_reg(call.type) if method.return_type != VoidType() else None
                self._emit(IRStaticCall(
                    cls=callee.target.symbol,
                    method=callee.symbol,
                    args=arg_ops,
                    destination=destination
                ))
                release_args()
                return destination
            else:
                # Instance method call
                destination = self._function_ctx.temp_reg(call.type) if callee.symbol.return_type != VoidType() else None
                target, owned = self._lower_expr(callee.target)
                self._emit(IRVirtualCall(
                    method=method,
                    target=target,
                    args=arg_ops,
                    destination=destination
                ))
                if owned:
                    self._release(target)
                release_args()
                return destination

        fatal_error(f"Unknown call expression type '{type(call)}'")
