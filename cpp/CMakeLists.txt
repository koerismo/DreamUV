cmake_minimum_required(VERSION 3.15...4.4)
project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)

find_package(Python 3.13
  REQUIRED COMPONENTS Interpreter Development.Module
  OPTIONAL_COMPONENTS Development.SABIModule
)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/ext/nanobind)
include_directories(_core ext/hotspotter/hammer/src)

nanobind_add_module(_core STABLE_ABI NB_STATIC LTO src/${SKBUILD_PROJECT_NAME}/_core.cpp)
nanobind_add_stub(
  _core_stub
  MODULE _core
  OUTPUT _core.pyi
  PYTHON_PATH $<TARGET_FILE_DIR:_core>
  DEPENDS _core
)

install(TARGETS _core LIBRARY DESTINATION ${SKBUILD_PROJECT_NAME})

