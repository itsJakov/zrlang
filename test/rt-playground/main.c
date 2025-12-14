#include <assert.h>
#include <stdio.h>

#include "zre.h"

extern Class Hasher;
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


uint64_t printObjHash(Instance* obj) {
    Instance* hasher = zre_alloc(&Hasher);
    ((void (*)(Instance*))zre_method_virtual(hasher, "init"))(hasher);

    ((void (*)(Instance*, Instance*))zre_method_virtual(obj, "hashInto"))(obj, hasher);
    uint64_t hash = ((uint64_t (*)(Instance*))zre_method_virtual(hasher, "finalize"))(hasher);
    printf("%s -> %lx\n", obj->cls->name, hash);

    zre_release(hasher);
    return hash;
}

void testHashing() {
    Instance* user0 = zre_alloc(&User);
    ((void (*)(Instance*))zre_method_virtual(user0, "init"))(user0);
    zre_field_set(user0, "username", (uint64_t)"jakovgz");

    Instance* user1 = zre_alloc(&User);
    ((void (*)(Instance*))zre_method_virtual(user1, "init"))(user1);
    zre_field_set(user1, "username", (uint64_t)"jakovgz");

    assert(printObjHash(user0) == printObjHash(user1));

    Instance* school = zre_alloc(&School);
    zre_field_set(school, "name", (uint64_t)"Aritmetika");

    zre_field_set(user0, "school", (uint64_t)school);
    zre_retain(school);

    assert(printObjHash(user0) != printObjHash(user1));

    extern Class Dictionary;
    Instance* dict = zre_alloc(&Dictionary); // Dictionary<User, School>
    ((void (*)(Instance*))zre_method_virtual(dict, "init"))(dict);

    // dict[user0] = school
    ((void (*)(Instance*, Instance*, Instance*))zre_method_virtual(dict, "set"))(dict, user0, school);

    // var schoolFromDict = dict[school]
    Instance* schoolFromDict = ((Instance* (*)(Instance*, Instance*))zre_method_virtual(dict, "get"))(dict, user0);
    assert(schoolFromDict == school);

    zre_release(schoolFromDict);
    zre_release(dict);
    zre_release(school);
    zre_release(user1);
    zre_release(user0);
}

int main(void) {
    testHashing();
    return 0;

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