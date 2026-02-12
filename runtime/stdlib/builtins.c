#include "zre.h"
#include "zre_utils.h"

#include <stdio.h>

void _zr_print(Instance* str) {
    zre_call(str, "printToStdout");
}

Instance* zre_string_literal(const char* s) {
    extern Class String;
    Instance* str = zre_alloc(&String);
    zre_call(str, "initWithCStrConstant", s);
    return str;
}