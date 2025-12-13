cmake_minimum_required(VERSION 3.31)
project(zrlang C)

set(CMAKE_C_STANDARD 11)

# QBE
add_custom_target(qbe ALL
        COMMAND make -C ${CMAKE_CURRENT_SOURCE_DIR}/qbe
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/qbe
        COMMENT "Building QBE"
)

# runtime
add_library(zrlang STATIC
        runtime/runtime.c
        runtime/Object.c
        runtime/stdlib/Array.c
        runtime/stdlib/LinkedList.c
        runtime/stdlib/RawBuffer.c
        runtime/stdlib/String.c)

target_include_directories(zrlang PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/runtime/include)

# rt-playground
add_executable(rt-playground
        test/rt-playground/main.c
        test/rt-playground/School.c
        test/rt-playground/User.c
        test/rt-playground/SuperUser.c
        test/rt-playground/UserArray.c
        test/rt-playground/DebugArray.c)

target_link_libraries(rt-playground zrlang)
