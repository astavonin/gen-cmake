#!/usr/bin/env python3

import sys, getopt, os


def print_usage():
    print("Usage:")
    print("\tgen-cmake [options]")
    print("Options:")
    print("\t-h show this message")
    print("\t-t <type>, --type=<type> generate project with <type>. Supported types:")
    print("\t\t app - generate execurable application")
    print("\t\t shared - generate dynamically linked library")
    print("\t\t static - generate archives of object files")
    print("\t -n <name>, --name=<name> project name")
    print("\t -s <standard>, --standard=<standard> C++ standard. C++11 is used by default")
    print("\t\t available options are: 03, 11, 14")
    print("\t-p <package1,package2,packageN>, --packages=<package1,package2,packageN> comma separated")
    print("\t\tlist of libraries to link with")


cpp_standard_template = \
    """set_property(TARGET ${{PROJECT_NAME}} PROPERTY CXX_STANDARD {0})
set_property(TARGET ${{PROJECT_NAME}} PROPERTY CXX_STANDARD_REQUIRED ON)"""

dst_type_app = \
    """add_executable(${{PROJECT_NAME}} ${{${{PROJECT_NAME}}_sources}})"""

dst_type_lib = \
    """add_library(${{PROJECT_NAME}} {1} ${{${{PROJECT_NAME}}_sources}})"""

makefile = \
    """# -----------------------------------------------------------------------------
# CMake project wrapper Makefile ----------------------------------------------
# -----------------------------------------------------------------------------

SHELL := /bin/bash
RM    := rm -rf
MKDIR := mkdir -p
LN := ln -s
BUILD_DIR ?= build
GENERATOR ?= Xcode

debug: BUILD_TYPE=Debug
debug: ./$(BUILD_DIR)/Makefile compile_commands.json
\t@ $(MAKE) -C $(BUILD_DIR) -j8

release: BUILD_TYPE=Release
release: ./$(BUILD_DIR)/Makefile compile_commands.json
\t@ $(MAKE) -C $(BUILD_DIR) -j8

all: ./$(BUILD_DIR)/Makefile compile_commands.json
\t@ $(MAKE) -C $(BUILD_DIR) -j8

compile_commands.json:
\t@ $(LN) $(BUILD_DIR)/compile_commands.json .

./$(BUILD_DIR)/Makefile:
\t@  ($(MKDIR) $(BUILD_DIR) > /dev/null)
\t@  (cd $(BUILD_DIR) > /dev/null 2>&1 && cmake .. -DCMAKE_BUILD_TYPE=$(BUILD_TYPE) -DCMAKE_EXPORT_COMPILE_COMMANDS=ON)

clean:
\t@ $(MAKE) -C $(BUILD_DIR) clean

bench:
\t@  (cd $(BUILD_DIR) > /dev/null && ctest -L bench --verbose)

test:
\t@  (cd $(BUILD_DIR) > /dev/null && ctest -L unit --verbose)

workspace:
\t@  ($(MKDIR) $(BUILD_DIR) > /dev/null)
\t@ (cd $(BUILD_DIR) > /dev/null && cmake -G $(GENERATOR) ..)

distclean:
\t@- $(RM) -rf ./$(BUILD_DIR)
"""

build_info = \
    """message("\\n--------------------------------\\n")
message("PROJECT NAME:\\t\\t${PROJECT_NAME}")
message("CMAKE_SYSTEM_NAME:\\t${CMAKE_SYSTEM_NAME}")
message("CMAKE_C_COMPILER:\\t${CMAKE_C_COMPILER}")
message("CMAKE_CXX_COMPILER:\\t${CMAKE_CXX_COMPILER}")
message("CMAKE_GENERATOR:\\t${CMAKE_GENERATOR}")
message("CMAKE_BUILD_TYPE:\\t${CMAKE_BUILD_TYPE}")
message("CMAKE_BINARY_DIR:\\t${CMAKE_BINARY_DIR}")
message("CMAKE_MODULE_PATH:\\t${CMAKE_MODULE_PATH}")
message("CMAKE_PREFIX_PATH:\\t${CMAKE_PREFIX_PATH}")
message("clang-tidy:\\t\\t${CLANG_TIDY}")
message("\\n--------------------------------\\n")

"""

cmake_template = \
    """cmake_minimum_required(VERSION 3.6)

if ( ${{CMAKE_SOURCE_DIR}} STREQUAL ${{CMAKE_BINARY_DIR}} )
    message( FATAL_ERROR "In-source builds not allowed. Please make a new directory and run CMake from there. You may need to remove CMakeCache.txt." )
endif()

set(PROJECT_NAME {0})
project(${{PROJECT_NAME}})

SET (CMAKE_LIBRARY_OUTPUT_DIRECTORY
        ${{PROJECT_BINARY_DIR}}/bin
        CACHE PATH
        "Single Directory for all"
    )

SET (CMAKE_RUNTIME_OUTPUT_DIRECTORY
        ${{PROJECT_BINARY_DIR}}/bin
        CACHE PATH
        "Single Directory for all"
    )

SET (CMAKE_ARCHIVE_OUTPUT_DIRECTORY
        ${{PROJECT_BINARY_DIR}}/lib
        CACHE PATH
        "Single Directory for all"
    )

{2}

{3}

# TODO: uncomment if have unit tests
# enable_testing()

find_program( CLANG_TIDY NAMES clang-tidy)
# NOTE: you can add search paths for example `PATHS /usr/local/opt/llvm/bin/`

{6}

set(${{PROJECT_NAME}}_sources main.cpp)

{4}

# NOTE: this will slow down compilation, but you'll have static code analysis :)
if(CLANG_TIDY)
    set_property(
        TARGET ${{PROJECT_NAME}}
        PROPERTY CXX_CLANG_TIDY "${{CLANG_TIDY}}")
endif()

{1}

{5}
"""


# {0} - project name
# {1} - C++ standard
# {2} - required packages
# {3} - includes
# {4} - project type (app, shared (lib), static (lib))
# {5} - linkages
# {6} - build information dump

class CMakeGenerator:
    project_type = ""
    project_name = ""
    standard = "11"
    packages = []

    def generate(self):
        cpp_standard = ""
        if not self.standard == "03":
            cpp_standard = cpp_standard_template.format(self.standard)

        incls, libs = self._gen_lib_usage()

        cmake_file_content = cmake_template.format(self.project_name, cpp_standard,
                                                   self._gen_packages(), incls,
                                                   self._gen_type_info(), libs,
                                                   build_info)

        with open("CMakeLists.txt", "w") as f:
            f.write(cmake_file_content)

        with open("Makefile", "w") as f:
            f.write(makefile)

    def is_complete(self):
        return self.project_type in ("app", "shared", "static") and not self.project_name == ""

    def _gen_packages(self):
        pkg_template = "find_package({0} REQUIRED)\n"
        out = ""
        for package in self.packages:
            req_package = pkg_template.format(package)
            out += req_package

        return out

    def _gen_lib_usage(self):
        link_libs = ""
        includes = ""
        for package in self.packages:
            link_libs += "${{{0}_LIBRARIES}} ".format(package)
            includes += "${{{0}_INCLUDE_DIRS}} ".format(package)

        if not link_libs == "":
            return f"target_include_directories(${{PROJECT_NAME}} {includes})", \
                   f"target_link_libraries(${{PROJECT_NAME}} {link_libs})"
        else:
            return "", ""

    def _gen_type_info(self):
        type_template = ""
        if self.project_type == "app":
            type_template = dst_type_app.format(self.project_name)
        elif self.project_type == "shared":
            type_template = dst_type_lib.format(self.project_name, "SHARED")
        elif self.project_type == "static":
            type_template = dst_type_lib.format(self.project_name, "STATIC")

        return type_template


def main():
    generator = CMakeGenerator()
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht:n:s:p:", ["type=", "name=", "standard=",
                                                               "packages="])
    except getopt.GetoptError as err:
        print("{}\n".format(err))
        print_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print_usage()
            sys.exit(2)
        elif opt in ("-t", "--type"):
            generator.project_type = arg
        elif opt in ("-n", "--name"):
            generator.project_name = arg
        elif opt in ("-s", "--standard"):
            generator.standard = arg
        elif opt in ("-p", "--packages"):
            generator.packages = [p.strip() for p in arg.split(",")]
        else:
            print("Invalid argument")
            print_usage()
            sys.exit(2)


    if os.path.exists("CMakeLists.txt") or os.path.exists("Makefile"):
        print("CMakeLists.txt or Makefile already exists")
        sys.exit(2)

    if not generator.is_complete():
        print_usage()
        sys.exit(2)

    generator.generate()


if __name__ == "__main__":
    main()
