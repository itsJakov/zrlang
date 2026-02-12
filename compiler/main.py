import subprocess
import sys

from compiler.llvm import LLVMIRGenerator
from compiler.sema import SemanticAnalyzer
from lang_ast import parse

INPUT = """
func main() {
    var logger = new Logger
    logger.log(3, "This will only be logged to file")
}

func isEven(x: Int) -> Bool {
    if x < 0 {
        print("treating negative number as 0, which is even")
        return true
    }
    return x % 2 == 0
}

class Logger {
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
    #res = subprocess.run(["clang", "-Wno-override-module", "ir.ll", "../cmake-build-debug/libzrlang.a", "-o", "prog"])
    if res.returncode != 0:
        sys.exit("Error in IR")

    # subprocess.run(["cc", "out.s", "-o", "prog"])