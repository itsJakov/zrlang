import subprocess
import sys

from compiler.llvm import LLVMIRGenerator
from compiler.sema import SemanticAnalyzer
from lang_ast import parse

INPUT = """
func isEven(x: Int) -> Bool {
    if x < 0 {
        print("treating negative number as 0, which is even")
        return true
    }
    return x % 2 == 0
}

class Logger {
    func doSomething() {
        var user = new User
        user.username = "field set test"
        
        var array = new Array
        array.append(user)
        
        if array.getIsEmpty() {
            print("Array is empty")
        } else {
            print("Array is not empty")
            var newUser = array.get(0)
            newUser.toString().printToStdout()
            newUser.testClass()
            newUser.greet("Hello from array")
            
            if false {
                print("will never happen")
            }  
        }
    }

    func shouldLog(level: Int) -> Bool {
        if level < 5 {
            return false
        }
        return isEven(level)
    }

    func log(level: Int, msg: String) {
        if self.shouldLog(level) {
            self.logToStdout(level, msg)
        }
        self.logToFile(level, msg)
    }
    
    func logToFile(level: Int, msg: String) {
        var newFile = new File
        newFile.initWithPath("log.txt")
        newFile.append(msg)
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

    with open("ir.ll", "w") as f:
        f.write(LLVMIRGenerator(result).generate())

    res = subprocess.run(["clang", "-Wno-override-module", "-S", "ir.ll", "-o", "out.s"])
    if res.returncode != 0:
        sys.exit("Error in IR")

    # subprocess.run(["cc", "out.s", "-o", "prog"])