import subprocess
import sys

from compiler.compile import compile_ir
from compiler.sema import SemanticAnalyzer
from lang_ast import parse

INPUT = """
class QBEUser : RootObject {
    var username: String
    
    func doSomething() {
        if 1 + 1 {
            var array = new Array
            self.doNesto(meow)
        }
    }
}
"""

if __name__ == "__main__":
    result = parse(INPUT)

    if not SemanticAnalyzer().analyze(result):
        sys.exit("Compilation failed due to semantic errors!")

    with open("ir.ssa", "w") as f:
        compile_ir(f, result)

    res = subprocess.run(["/bin/bash", "-c", "\"../qbe/qbe\" -o out.s ir.ssa"])
    if res.returncode != 0:
        sys.exit("Error in IR")

    # subprocess.run(["cc", "out.s", "-o", "prog"])