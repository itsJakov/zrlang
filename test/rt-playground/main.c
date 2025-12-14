#include <stdio.h>

#include "zre.h"

extern Class User;
extern Class SuperUser;
extern Class School;
extern Class Array;

void printObject(Instance* obj) {
    // var str = newUser.toString()
    Instance* str = ((Instance* (*)(Instance*))zre_method_virtual(obj, "toString"))(obj);

    // str.printToStdout()
    ((void (*)(Instance*))zre_method_virtual(str, "printToStdout"))(str);

    zre_release(str); // [ARC] Exiting block
}

int main(void) {
    // var newUser = User.init()
    Instance* newUser = zre_alloc(&SuperUser);
    ((void (*)(Instance*))zre_method_virtual(newUser, "init"))(newUser);

    // newUser._username = "jakovgz"
    zre_field_set(newUser, "username", (uint64_t)"jakovgz");

    // newUser._title = "Dr. Sc."
    zre_field_set(newUser, "title", (uint64_t)"Dr. Sc.");

    // newUser.greet("Hello")
    ((void (*)(Instance*, char*))zre_method_virtual(newUser, "greet"))(newUser, "Hello");

    // newUser.testClass()
    ((void (*)(Instance*))zre_method_virtual(newUser, "testClass"))(newUser);

    printObject(newUser);

    {
        // var school = School.init()
        Instance* school = zre_alloc(&School);

        // school._name = "Aritmetika"
        zre_field_set(school, "name", (uint64_t)"Aritmetika");

        // newUser._school = school
        zre_field_set(newUser, "school", (uint64_t)school);
        zre_retain(school); // [ARC] Strong reference

        zre_release(school); // [ARC] Exiting block
    }

    {
        // var allUsers = Array.init()
        Instance* allUsers = zre_alloc(&Array);
        ((void (*)(Instance*))zre_method_virtual(allUsers, "init"))(allUsers);

        // allUsers.append(newUser)
        ((void (*)(Instance*, Instance*))zre_method_virtual(allUsers, "append"))(allUsers, newUser);

        // var firstItemInArray = allUsers.get(0)
        Instance* firstItemInArray = ((Instance* (*)(Instance*, uint64_t))zre_method_virtual(allUsers, "get"))(allUsers, 0);

        // firstItemInArray.testClass()
        ((void (*)(Instance*))zre_method_virtual(firstItemInArray, "testClass"))(firstItemInArray);

        zre_release(firstItemInArray); // [ARC] Exiting block
        zre_release(allUsers); // [ARC] Exiting block
    }

    zre_release(newUser); // [ARC] Exiting block
    return 0;
}