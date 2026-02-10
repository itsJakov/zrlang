import subprocess
import sys

from compiler.compile import compile_ir
from compiler.sema import SemanticAnalyzer
from lang_ast import parse

INPUT = """
class Logger {
    func doSomething() {
        if 1 > 0 {
            print("meow")
            return
            print("never")
        }
        if (new Array).getIsEmpty() {
            print("expected")
            return
        }
        return
        print("meow")
    }

    func log(level: Int, msg: String) {
        if level % 2 == 0 {
            self.logToStdout(level, msg)
        }
        self.logToFile(level, msg)
    }
    
    func logToFile(level: Int, msg: String) {
        
    }
    
    func logToStdout(level: Int, msg: String) {
        msg.printToStdout()
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