import subprocess
import sys

from compiler.IRLowerer import IRLowerer
from lang_ast import parse
from compiler import SemanticAnalyzer, LLVMIRGenerator

INPUT = """
func main() -> Int {
    var logger = Logger.new()
    
    print("=== Logging with message level over threshold ===")
    logger.log(5, "This is a log message :)")
    
    print("=== Logging with message level under threshold ===")
    logger.log(logger.threshold - 1, "You will never see this log message :(")
    
    print("=== Testing all services ===")
    logger.testAllServices()
    
    return 0
}

class LoggerService {
    func log(message: String) {
    }
    
    func test() {
        print("Testing Service: ".concat(self.toString()))
        self.log("TEST MESSAGE")
    }
}

class ConsoleLoggerService : LoggerService {
    override func log(message: String) {
        print(message)
    }
}

class FileLoggerService : LoggerService {
    override func log(message: String) {
        var newFile = new File
        newFile.initWithPath("log.txt")
        newFile.append(message)
    }
}

class Logger {
    var services: Array
    var threshold: Int
    
    static func new() -> Logger {
        var logger = new Logger
        logger.init()
        logger.threshold = 2
        
        logger.addService(new ConsoleLoggerService)
        logger.addService(new FileLoggerService)
        
        return logger
    }
    
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
    
    func testAllServices() {
        print("Testing all services in ".concat(self.toString()))
        self.services.get(0).test()
        self.services.get(1).test()
    }
    
    override func toString() -> String {
        return super.toString().concat(" (Custom toString)")
    }
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

    # Phase 4: LLVM IR codegen
    with open("ir.ll", "w") as f:
        f.write(LLVMIRGenerator(ir_funcs, ir_classes).generate())

    # Phase 5: Compile with clang
    res = subprocess.run(["clang", "-Wno-override-module", "-S", "ir.ll", "-o", "out.s"])
    #res = subprocess.run(["clang", "-Wno-override-module", "ir.ll", "../cmake-build-debug/libzrlang.a", "-o", "prog"])
    if res.returncode != 0:
        sys.exit("Error in IR")