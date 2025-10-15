# CMakeLists.txt for FormoTensor Python Bridge
cmake_minimum_required(VERSION 3.22 FATAL_ERROR)

# Find Python and pybind11
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

message(STATUS "Python3 found: ${Python3_EXECUTABLE}")
message(STATUS "Python3 include: ${Python3_INCLUDE_DIRS}")
message(STATUS "pybind11 found: ${pybind11_VERSION}")

# Create Python extension module
pybind11_add_module(formotensor_bridge 
    formotensor_bridge.cpp
)

# Set C++ standard
target_compile_features(formotensor_bridge PRIVATE cxx_std_20)

# Include directories - use the same as the main project
target_include_directories(formotensor_bridge PRIVATE
    ${CMAKE_SOURCE_DIR}/src
    ${CUDA_QUANTUM_PATH}/include
    ${CUTENSORNET_ROOT}/include
    ${CUTENSOR_ROOT}/include
    ${EIGEN3_INCLUDE_DIR}
)

# Link against CUDA libraries
target_link_libraries(formotensor_bridge PRIVATE
    CUDA::cudart
    ${CUTENSORNET_LIB}
    ${CUTENSOR_LIB}
)

# Set RPATH for finding shared libraries at runtime
set_target_properties(formotensor_bridge PROPERTIES
    BUILD_RPATH "${CMAKE_BINARY_DIR}/lib:${CUDA_QUANTUM_PATH}/lib"
    INSTALL_RPATH "${CUDA_QUANTUM_PATH}/lib:${Python3_SITELIB}"
    BUILD_WITH_INSTALL_RPATH FALSE
    INSTALL_RPATH_USE_LINK_PATH TRUE
)

# Install the Python module to Python site-packages
install(TARGETS formotensor_bridge
    LIBRARY DESTINATION ${Python3_SITELIB}
    COMPONENT python
)

message(STATUS "Python module will be installed to: ${Python3_SITELIB}")

