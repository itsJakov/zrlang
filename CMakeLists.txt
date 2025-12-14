cmake_minimum_required(VERSION 3.31)
project(zrlang C)

set(CMAKE_C_STANDARD 11)

include(FetchContent)

# xxHash
FetchContent_Declare(
        xxhash
        GIT_REPOSITORY https://github.com/Cyan4973/xxHash.git
        GIT_TAG v0.8.3
)
FetchContent_MakeAvailable(xxhash)


# QBE
add_custom_target(qbe ALL
        COMMAND make -C ${CMAKE_CURRENT_SOURCE_DIR}/qbe
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/qbe
        COMMENT "Building QBE"
)

# runtime
add_library(zrlang STATIC
        runtime/stb.c
        runtime/runtime.c
        runtime/Object.c
        runtime/stdlib/String.c
        runtime/stdlib/Array.c
        runtime/stdlib/Dictionary.c
        runtime/stdlib/String.c
        runtime/Hasher.c)

target_include_directories(zrlang PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/runtime/include)

target_link_libraries(zrlang PRIVATE xxhash)

# rt-playground
add_executable(rt-playground
        test/rt-playground/main.c
        test/rt-playground/School.c
        test/rt-playground/User.c
        test/rt-playground/SuperUser.c)

target_link_libraries(rt-playground zrlang)
