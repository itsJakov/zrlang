#include <assert.h>
#include <stdio.h>

#include "zre.h"
#include "zre_utils.h"

extern Class Hasher;
extern Class User;
extern Class SuperUser;
extern Class School;
extern Class Array;

void testHashing() {
    Instance* user0 = zre_alloc(&User);
    ((void (*)(Instance*))zre_method_virtual(user0, "init"))(user0);
    zre_field_set(user0, "username", (uint64_t)"jakovgz");

    Instance* user1 = zre_alloc(&User);
    ((void (*)(Instance*))zre_method_virtual(user1, "init"))(user1);
    zre_field_set(user1, "username", (uint64_t)"jakovgz");

    assert(zre_hash(user0) == zre_hash(user1));

    Instance* school = zre_alloc(&School);
    zre_field_set(school, "name", (uint64_t)"Aritmetika");

    zre_field_set(user0, "school", (uint64_t)school);
    zre_retain(school);

    assert(zre_hash(user0) != zre_hash(user1));

    extern Class Dictionary;
    Instance* dict = zre_alloc(&Dictionary); // Dictionary<User, School>
    ((void (*)(Instance*))zre_method_virtual(dict, "init"))(dict);

    // dict[user0] = school
    ((void (*)(Instance*, Instance*, Instance*))zre_method_virtual(dict, "set"))(dict, user0, school);

    // var schoolFromDict = dict[user0]
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
}