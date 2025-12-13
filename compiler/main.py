import subprocess
import sys

from compiler import compile_ir
from lang_ast import parse

INPUT = """
func main() {
    var falseCon = Math.sub(5, 5) 
    var trueCon = Math.sub(5, 0)
    
    if falseCon {
        print "yes"
    } else if trueCon {
        print "yes, but..."
    } else {
        print "no"
    }
    
    print "end"
}
"""

if __name__ == "__main__":
    result = parse(INPUT)

    with open("ir.ssa", "w") as f:
        compile_ir(f, result)

    res = subprocess.run(["/bin/bash", "-c", "\"/Users/jakovgz/Downloads/qbe/qbe\" -o out.s ir.ssa"])
    if res.returncode != 0:
        sys.exit("Error in IR")

    # subprocess.run(["cc", "out.s", "-o", "prog"])