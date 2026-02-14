#include <assert.h>
#include <stdio.h>

#include "zre.h"
#include "zre_utils.h"

extern Class User;
extern Class School;

void testHashing() {
    Instance* user0 = zre_alloc(&User);
    zre_call(user0, "init");
    zre_field_set(user0, "username", zstr("jakovgz"));

    zre_call(user0, "testClass");

    Instance* user1 = zre_alloc(&User);
    zre_call(user1, "init");
    zre_field_set(user1, "username", zstr("jakovgz"));

    Instance* user2 = zre_alloc(&User);
    zre_call(user2, "init");
    zre_field_set(user2, "username", zstr("itsjakov"));

    assert(zre_hash(user0) == zre_hash(user1));
    assert(zre_hash(user0) != zre_hash(user2));

    Instance* school = zre_alloc(&School);
    zre_field_set(school, "name", zstr("Aritmetika"));
    zre_field_set(user0, "school", school);
    zre_retain(school);
    assert(zre_hash(user0) != zre_hash(user1));

    zre_release(school);
    zre_release(user2);
    zre_release(user1);
    zre_release(user0);
}

void testDictionary() {
    extern Class Dictionary;

    Instance* user0 = zre_alloc(&User);
    zre_call(user0, "init");
    zre_field_set(user0, "username", zstr("jakovgz"));

    Instance* user0a = zre_alloc(&User);
    zre_call(user0a, "init");
    zre_field_set(user0a, "username", zstr("jakovgz"));

    Instance* user1 = zre_alloc(&User);
    zre_call(user1, "init");
    zre_field_set(user1, "username", zstr("itsjakov"));

    Instance* usernameToUser = zre_alloc(&Dictionary); // Dictionary<String, User>
    zre_call(usernameToUser, "init");
    zre_call(usernameToUser, "set", zre_field_get_obj(user0, "username"), user0);
    zre_call(usernameToUser, "set", zre_field_get_obj(user1, "username"), user1);

    Instance* retrievedUser0 = zre_call(usernameToUser, "get", zre_field_get_obj(user0, "username"));
    Instance* retrievedUser1 = zre_call(usernameToUser, "get", zre_field_get_obj(user1, "username"));
    assert(retrievedUser0 == user0);
    assert(retrievedUser1 == user1);

    zre_call(usernameToUser, "set", zstr("jakovgz"), user0a);
    Instance* retrievedUser0a = zre_call(usernameToUser, "get", zstr("jakovgz"));
    assert(retrievedUser0a == user0a);

    retrievedUser0 = zre_call(usernameToUser, "get", zre_field_get_obj(user0, "username"));
    assert(retrievedUser0 == user0a);
}

int main(void) {
    testHashing();
    testDictionary();
    return 0;
}
