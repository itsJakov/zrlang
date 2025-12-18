cmake_minimum_required(VERSION 3.31)
project(zrlang C)

set(CMAKE_C_STANDARD 11)

include(FetchContent)

# QBE
add_custom_target(qbe ALL
        COMMAND make -C ${CMAKE_CURRENT_SOURCE_DIR}/qbe
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/qbe
        COMMENT "Building QBE"
)

# runtime
add_library(zrlang STATIC
        runtime/lib/stb.c
        runtime/lib/xxhash.c
        runtime/runtime.c
        runtime/stdlib/builtins.c
        runtime/stdlib/Object.c
        runtime/stdlib/String.c
        runtime/stdlib/Array.c
        runtime/stdlib/Dictionary.c
        runtime/stdlib/String.c
        runtime/stdlib/Hasher.c)

target_include_directories(zrlang PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/runtime/lib)

target_include_directories(zrlang PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/runtime/include)

# rt-playground
add_executable(rt-playground
        test/rt-playground/main.c
        test/rt-playground/School.c
        test/rt-playground/User.c
        test/rt-playground/SuperUser.c)

target_link_libraries(rt-playground zrlang)
