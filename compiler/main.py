import subprocess
import sys

from compiler.compile import compile_ir
from lang_ast import parse

INPUT = """
class QBEUser : RootObject {
    var firstName: String
    
    func doSomething() {
        var name = new User
        var someInt = 0
        self.greet(2, self.firstName()).string.prefix(someInt)
    }
}
"""

if __name__ == "__main__":
    result = parse(INPUT)

    with open("ir.ssa", "w") as f:
        compile_ir(f, result)

    res = subprocess.run(["/bin/bash", "-c", "\"../qbe/qbe\" -o out.s ir.ssa"])
    if res.returncode != 0:
        sys.exit("Error in IR")

    # subprocess.run(["cc", "out.s", "-o", "prog"])