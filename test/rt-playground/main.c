#include <assert.h>
#include <stdio.h>

#include "zre.h"
#include "zre_utils.h"

extern Class User;
extern Class School;
extern Class Array;

void testHashing() {
    Instance* user0 = zre_alloc(&User);
    zre_call(user0, "init");
    zre_field_set(user0, "username", (uint64_t)zstr("jakovgz"));

    Instance* user1 = zre_alloc(&User);
    zre_call(user1, "init");
    zre_field_set(user1, "username", (uint64_t)zstr("jakovgz"));

    Instance* user2 = zre_alloc(&User);
    zre_call(user2, "init");
    zre_field_set(user2, "username", (uint64_t)zstr("itsjakov"));

    assert(zre_hash(user0) == zre_hash(user1));
    assert(zre_hash(user0) != zre_hash(user2));

    Instance* school = zre_alloc(&School);
    zre_field_set(school, "name", (uint64_t)zstr("Aritmetika"));
    zre_field_set(user0, "school", (uint64_t)school);
    zre_retain(school);
    assert(zre_hash(user0) != zre_hash(user1));

    zre_release(school);
    zre_release(user2);
    zre_release(user1);
    zre_release(user0);
}

int main(void) {
    testHashing();
    return 0;
}