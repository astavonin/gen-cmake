# gen-cmake
CMakeLists.txt file generator

Usage:
	gen-cmake [options]
Options:
	-h show this message
	-t <type>, --type=<type> generate project with <type>. Supported types:
		 app - generate execurable application
	 -n <name>, --name=<name> project name
	 -s <standard>, --standard=<standard> C++ standard. C++11 is used by default
		 available options are: 03, 11, 14
	-p <package1,package2,packageN>, --packages=<package1,package2,packageN> comma separated
		list of libraries to link with

Example (will generate CMakeLists.txt with C++11 and BOOST libray linkage):

> python3 gen-cmake.py -t app -n test_app -s 11 -p boost
