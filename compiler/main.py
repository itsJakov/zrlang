import subprocess
import sys

from compiler.llvm import LLVMIRGenerator
from compiler.sema import SemanticAnalyzer
from lang_ast import parse

INPUT = """
func main() -> Int {
    var logger = new Logger
    logger.init()
    logger.threshold = 2
    
    logger.addService(new ConsoleLoggerService)
    logger.addService(new FileLoggerService)
    
    logger.log(5, "This is a log message :)")
    print(logger)
    
    return 0
}

class LoggerService {
    func log(message: String) {
    }
    
    func test() {
        self.log("TEST MESSAGE")
    }
}

class ConsoleLoggerService : LoggerService {
    func log(message: String) {
        print(message)
    }
}

class FileLoggerService : LoggerService {
    func log(message: String) {
        var newFile = new File
        newFile.initWithPath("log.txt")
        newFile.append(message)
    }
}

class Logger {
    var services: Array
    var threshold: Int
    
    func init() {
        self.services = new Array
    }
    
    func addService(service: LoggerService) {
        self.services.append(service)
    }
    
    func log(level: Int, message: String) {
        if level >= self.threshold {
            self.services.get(0).log(message)
            self.services.get(1).log(message)
        } else {
            print("Log level too low, skipping log")
        }
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