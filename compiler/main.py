import subprocess
import sys

from compiler.IR import ir_to_str
from compiler.IRLowerer import IRLowerer
from lang_ast import parse
from compiler import SemanticAnalyzer, LLVMIRGenerator

INPUT = """
class _ArrayIterator {
    var arr: Array
    var idx: Int
    
    func initWithArray(arr: Array) {
        self.arr = arr
        self.idx = 0
    }
    
    func hasNext() -> Bool {
        return self.idx < self.arr.getCount()   
    }
    
    func next() -> Object {
        var obj = self.arr.get(self.idx)
        self.idx = self.idx + 1
        return obj
    }
}

class IterableArray : Array {
    func iterator() -> _ArrayIterator {
        var iter = new _ArrayIterator
        iter.initWithArray(self)
        return iter
    } 
}

func main() -> Int {
    var list = new IterableArray
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