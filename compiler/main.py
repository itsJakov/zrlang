import subprocess
import sys

from compiler.compile import compile_ir
from compiler.sema import SemanticAnalyzer
from lang_ast import parse

INPUT = """
class QBEUser : RootObject {
    var username: String
    
    func doSomething() {
        var user = new QBEUser
        user.username = "test"
        
        var array = new Array
        array.append(user)
        
        if array.getIsEmpty() {
            print("Array is empty")
        } else {
            print("Array is not empty")
            array.get(0).toString().printToStdout()
        }
            
        print("Method End")
    }
}
"""

if __name__ == "__main__":
    result = parse(INPUT)

    SemanticAnalyzer().analyze(result)

    with open("ir.ssa", "w") as f:
        compile_ir(f, result)

    res = subprocess.run(["/bin/bash", "-c", "\"../qbe/qbe\" -o out.s ir.ssa"])
    if res.returncode != 0:
        sys.exit("Error in IR")

    # subprocess.run(["cc", "out.s", "-o", "prog"])