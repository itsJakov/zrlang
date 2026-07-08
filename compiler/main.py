import subprocess
import sys

from compiler.IR import ir_to_str
from compiler.IRLowerer import IRLowerer
from lang_ast import parse
from compiler import SemanticAnalyzer, LLVMIRGenerator

INPUT = """
func main() -> Int {
    var list = new Array
    list.append("Hello,")
    list.append("world!")
    list.append("This")
    list.append("is")
    list.append("my")
    list.append("list.")

    for str in list {
        print(str)
    }

    return 0
}
"""

if __name__ == "__main__":
    # Phase 1: Parsing
    result = parse(INPUT)

    # Phase 2: Semantic Analysis
    symbols = SemanticAnalyzer().analyze(result)
    if symbols is None:
        sys.exit("Compilation failed due to semantic errors!")
    func_symbols, class_symbols = symbols

    # Phase 3: Lowering to IR
    ir_funcs, ir_classes = IRLowerer().lower(func_symbols, class_symbols)
    with open("ir.txt", "w") as f:
        f.write(ir_to_str(ir_funcs, ir_classes))

    # Phase 4: LLVM IR codegen
    with open("ir.ll", "w") as f:
        f.write(LLVMIRGenerator(ir_funcs, ir_classes).generate())

    # Phase 5: Compile with clang
    #res = subprocess.run(["clang", "-Wno-override-module", "-S", "ir.ll", "-o", "out.s"])
    res = subprocess.run(["clang", "-Wno-override-module", "ir.ll", "../cmake-build-debug/libzrlang.a", "-o", "prog"])
    if res.returncode != 0:
        sys.exit("Error in IR")