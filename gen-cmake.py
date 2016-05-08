#!/usr/bin/env python3

import sys, getopt


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
    """add_executable(${{PROJECT_NAME}} ${{{0}_sources}})"""

dst_type_lib = \
    """add_library(${{PROJECT_NAME}} {1} ${{{0}_sources}})"""

cmake_template = \
    """cmake_minimum_required(VERSION 3.4)

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

set({0}_sources main.cpp)

{4}

{1}

{5}
"""


# {0} - project name
# {1} - C++ standard
# {2} - required packages
# {3} - includes
# {4} - project type (app, shared (lib), static (lib))
# {5} - linkages

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
                                                   self._gen_type_info(), libs)

        with open("CMakeLists.txt", "w") as f:
            f.write(cmake_file_content)

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
            return "include_directories({0})".format(includes), \
                    "target_link_libraries({0} {1})".format(self.project_name, link_libs)
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

    if not generator.is_complete():
        print_usage()
        sys.exit(2)

    generator.generate()


if __name__ == "__main__":
    main()
