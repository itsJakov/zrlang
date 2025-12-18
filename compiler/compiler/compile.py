import sys
from typing import Optional

from compiler.unit_context import UnitContext
from lang_ast import ClassDecl, ClassField, MethodDecl, VarStmt, _Statement, IntExpr, LocalExpr, AllocExpr, CallStmt, \
    MemberExpr, _Expression, CallExpr, StringExpr, AssignStmt, IfStmt

depth = 0 # TODO

def expr_into_local(f, expr: _Expression, unit_ctx: UnitContext, *, local: Optional[str] = None) -> str:
    def get_temp_sym() -> str: # TODO: No ARC...
        if local is not None: return f"%{local}"
        global depth
        sym = f"%_temp{depth}"
        depth += 1
        return sym

    if isinstance(expr, IntExpr):
        return f"{expr.value}"
    if isinstance(expr, StringExpr):
        temp = get_temp_sym()
        f.write(f"\t{temp} =l add $strings, {unit_ctx.string_offset(expr.value)}\n")
        return temp
    elif isinstance(expr, LocalExpr):
        return f"%{expr.local}"
    elif isinstance(expr, MemberExpr):
        sym = expr_into_local(f, expr.expr, unit_ctx)
        temp = get_temp_sym()
        f.write(f"\t%_str =l add $strings, {unit_ctx.string_offset(expr.member)}\n")
        f.write(f"\t{temp} =l call $zre_get_field(l {sym}, l %_str)\n")
        return temp
    elif isinstance(expr, CallExpr):
        call = expr
        if isinstance(call.callee, MemberExpr):
            sym = expr_into_local(f, call.callee.expr, unit_ctx)
            args = ", ".join(f"l {expr_into_local(f, symbol, unit_ctx)}" for symbol in call.args)

            f.write(f"\t%_str =l add $strings, {unit_ctx.string_offset(call.callee.member)}\n")
            f.write(f"\t%_fn =l call $zre_method_virtual(l {sym}, l %_str)\n")
            temp = get_temp_sym()
            f.write(f"\t{temp} =l call %_fn(l {sym}, {args})\n")
            return temp
        else:
            sys.exit(f"Not a callable stmt {call.callee}!")
    elif isinstance(expr, AllocExpr):
        temp = get_temp_sym()
        f.write(f"\t{temp} =l call $zre_alloc(l ${expr.cls_name})\n")
        return temp
    else:
        sys.exit(f"Unsupported expr {expr}")

def compile_block(f, block: list[_Statement], unit_ctx: UnitContext):
    for stmt in block:
        if isinstance(stmt, VarStmt):
            if stmt.expr is None:
                f.write(f"\t%{stmt.local} =l copy 0\n")
            elif isinstance(stmt.expr, IntExpr):
                f.write(f"\t%{stmt.local} =l copy {stmt.expr.value}\n")
            elif isinstance(stmt.expr, LocalExpr):
                f.write(f"\t%{stmt.local} =l copy %{stmt.expr.local}\n")
            else:
                expr_into_local(f, stmt.expr, unit_ctx, local=stmt.local)

        elif isinstance(stmt, CallStmt):
            expr_into_local(f, stmt.call, unit_ctx)

        elif isinstance(stmt, AssignStmt):
            if isinstance(stmt.assignee, LocalExpr):
                if isinstance(stmt.value, IntExpr):
                    f.write(f"\t%{stmt.assignee.local} =l copy {stmt.value.value}\n")
                elif isinstance(stmt.value, LocalExpr):
                    f.write(f"\t%{stmt.assignee.local} =l copy %{stmt.value.local}\n")
                else:
                    expr_into_local(f, stmt.value, unit_ctx, local=stmt.assignee.local)
            elif isinstance(stmt.assignee, MemberExpr):
                instance_sym = expr_into_local(f, stmt.assignee.expr, unit_ctx)
                field_name = stmt.assignee.member
                value_sym = expr_into_local(f, stmt.value, unit_ctx)

                f.write(f"\t%_str =l add $strings, {unit_ctx.string_offset(field_name)}\n")
                f.write(f"\tcall $zre_field_set(l {instance_sym}, l %_str, l {value_sym})\n")
            else:
                sys.exit(f"Not an assignable expression! {stmt.assignee}")

        elif isinstance(stmt, IfStmt):
            f.write(f"\tjnz {expr_into_local(f, stmt.condition, unit_ctx)}, @if0_true, @if0_false\n")

            f.write(f"@if0_true\n")
            compile_block(f, stmt.block, unit_ctx)
            f.write(f"\tjmp @if0_end\n")

            f.write(f"@if0_false\n")
            if stmt.elseBlock is not None:
                compile_block(f, stmt.elseBlock, unit_ctx)

            f.write(f"@if0_end\n")

        else:
            sys.exit(f"Statement not supported yet {stmt}")

def compile_method(f, method: MethodDecl, cls: ClassDecl, unit_ctx: UnitContext):
    f.write(f"function l ${cls.name}_{method.name}(l %self) {{\n")
    f.write("@start\n")
    compile_block(f, method.block, unit_ctx)
    f.write("\tret\n")
    f.write("}\n")

# TODO: Clang throws a tantrum if _fields or _instanceMethods are empty
def compile_cls(f, cls: ClassDecl, unit_ctx: UnitContext):
    f.write(f"# ==== \"{cls.name}\" Class Definition ==== \n")
    fields: list[ClassField] = list(filter(lambda x: isinstance(x, ClassField), cls.members))
    f.write(f"data ${cls.name}_fields = {{\n")
    for field in fields:
        f.write(f"\tl {unit_ctx.string_sym(field.name)}, l 0,\n")
    f.write("}\n")

    methods: list[MethodDecl] = list(filter(lambda x: isinstance(x, MethodDecl), cls.members))
    f.write(f"data ${cls.name}_instanceMethods = {{\n")
    for method in methods:
        f.write(f"\tl {unit_ctx.string_sym(method.name)}, l ${cls.name}_{method.name},\n")
    f.write("}\n")

    f.write(f"export data ${cls.name} = {{\n")
    f.write(f"\tl {unit_ctx.string_sym(cls.name)},\n")
    if cls.super is None:
        f.write(f"\tl 0,\n")
    else:
        f.write(f"\tl ${cls.super},\n")
    f.write(f"\tl {len(fields)}, l ${cls.name}_fields,\n")
    f.write(f"\tl 0, l 0,\n")
    f.write(f"\tl {len(methods)}, l ${cls.name}_instanceMethods\n")
    f.write("}\n\n")

    f.write(f"# ==== \"{cls.name}\" Methods ==== \n")
    for method in methods:
        compile_method(f, method, cls, unit_ctx)
    f.write("\n")

def compile_ir(f, classes: list[ClassDecl]):
    f.write("# ==== Generated by zrlang ==== \n\n")

    unit_ctx = UnitContext()

    for cls in classes:
        compile_cls(f, cls, unit_ctx)

    f.write("# ==== String Data ==== \n")
    f.write(f"data $strings = {{ b \"{unit_ctx.string_data}\" }}")