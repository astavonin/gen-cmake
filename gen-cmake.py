#!/usr/bin/env python3

import sys, getopt


def print_usage():
    print("Usage:")
    print("\tgen-cmake [options]")
    print("Options:")
    print("\t-h show this message")
    print("\t-t <type>, --type=<type> generate project with <type>. Supported types:")
    print("\t\t app - generate execurable application")
    print("\t -n <name>, --name=<name> project name")
    print("\t -s <standard>, --standard=<standard> C++ standard. C++11 is used by default")
    print("\t\t available options are: 03, 11, 14")
    print("\t-p <package1,package2,packageN>, --packages=<package1,package2,packageN> comma separated")
    print("\t\tlist of libraries to link with")


cpp_standard_template = \
    """set_property(TARGET ${{PROJECT_NAME}} PROPERTY CXX_STANDARD {0})
set_property(TARGET ${{PROJECT_NAME}} PROPERTY CXX_STANDARD_REQUIRED ON)"""

cmake_app_template = \
    """cmake_minimum_required(VERSION 3.4)

project({0})

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

set({0}_sources main.cpp)

add_executable({0} ${{{0}_sources}})

{1}

{3}
"""


# {0} - project name
# {1} - C++ standard
# {2} - required packages
# {3} - includes and linkage

class CmakeGenerator:
    project_type = ""
    project_name = ""
    standard = "11"
    packages = []

    def generate(self):
        cpp_standard = ""
        if not self.standard == "03":
            cpp_standard = cpp_standard_template.format(self.standard)

        cmake_file_content = cmake_app_template.format(self.project_name, cpp_standard,
                                               self._gen_packages(), self._gen_lib_usage())

        with open("CMakeLists.txt", "w") as f:
            f.write(cmake_file_content)

    def is_complete(self):
        return not (self.project_type == "" or self.project_name == "")

    def _gen_packages(self):
        pkg_template = "find_package({0} REQUIRED)\n"
        out = ""
        for package in self.packages:
            req_package = pkg_template.format(package)
            out += req_package

        return out

    def _gen_lib_usage(self):
        link_template = "target_link_libraries({0} {1})\n" \
                        "include_directories({2})"
        link_libs = ""
        includes = ""
        out = ""
        for package in self.packages:
            link_libs += "${{{0}_LIBRARIES}} ".format(package)
            includes += "${{{0}_INCLUDE_DIRS}} ".format(package)

        if not link_libs == "":
            out = link_template.format(self.project_name, link_libs, includes)

        return out


def main():
    generator = CmakeGenerator()
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
