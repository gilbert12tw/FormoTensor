cmake_minimum_required(VERSION 3.24 FATAL_ERROR)
project(FormoTensor VERSION 1.0.0 LANGUAGES CXX CUDA)

# Set C++ standard - require C++20 for full compatibility
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Check compiler version
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    if(CMAKE_CXX_COMPILER_VERSION VERSION_LESS "11.0")
        message(FATAL_ERROR "GCC ${CMAKE_CXX_COMPILER_VERSION} does not fully support C++20. Please install GCC 11+ using: conda install -c conda-forge gcc=11 gxx=11")
    endif()
endif()

# Position independent code
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-ctad-maybe-unsupported")

# Check required environment variables
if(NOT DEFINED ENV{CUDA_QUANTUM_PATH})
    message(FATAL_ERROR "CUDA_QUANTUM_PATH environment variable is not set. Please set it to your CUDA-Q installation path.")
endif()

set(CUDA_QUANTUM_PATH $ENV{CUDA_QUANTUM_PATH})
message(STATUS "Using CUDA_QUANTUM_PATH: ${CUDA_QUANTUM_PATH}")

# Find required packages
find_package(NVQIR REQUIRED HINTS "${CUDA_QUANTUM_PATH}/lib/cmake/nvqir")
find_package(CUDAToolkit REQUIRED)

# Find Eigen3 library
find_package(Eigen3 QUIET)
if(NOT Eigen3_FOUND)
    # Try to find Eigen3 in common locations
    find_path(EIGEN3_INCLUDE_DIR 
        NAMES Eigen/Dense
        HINTS 
            ${CUDA_QUANTUM_PATH}/include
            $ENV{CONDA_PREFIX}/include/eigen3
            $ENV{CONDA_PREFIX}/include
            /usr/include/eigen3
            /usr/local/include/eigen3
    )
    
    if(EIGEN3_INCLUDE_DIR)
        message(STATUS "Found Eigen3 headers: ${EIGEN3_INCLUDE_DIR}")
        set(EIGEN3_FOUND TRUE)
    else()
        message(FATAL_ERROR "Eigen3 not found. Please install it with: conda install -c conda-forge eigen")
    endif()
endif()

# Find cuTensor library
set(CUTENSOR_ROOT $ENV{CUTENSOR_ROOT})
if(NOT CUTENSOR_ROOT)
    set(CUTENSOR_ROOT $ENV{CONDA_PREFIX})
endif()

find_library(CUTENSOR_LIB
    NAMES cutensor libcutensor.so.2
    HINTS 
        ${CUTENSOR_ROOT}/lib64
        ${CUTENSOR_ROOT}/lib
        ${CUTENSOR_ROOT}/lib64/${CUDAToolkit_VERSION_MAJOR}
        ${CUTENSOR_ROOT}/lib/${CUDAToolkit_VERSION_MAJOR}
        ${CUDA_QUANTUM_PATH}/lib
        $ENV{CONDA_PREFIX}/lib
        $ENV{CONDA_PREFIX}/lib/python*/site-packages/cutensor/lib
    REQUIRED
)

# Find cuTensorNet library
set(CUTENSORNET_ROOT $ENV{CUTENSORNET_ROOT})
if(NOT CUTENSORNET_ROOT)
    set(CUTENSORNET_ROOT $ENV{CONDA_PREFIX})
endif()

find_library(CUTENSORNET_LIB
    NAMES cutensornet libcutensornet.so.2
    HINTS 
        ${CUTENSORNET_ROOT}/lib64
        ${CUTENSORNET_ROOT}/lib
        ${CUTENSORNET_ROOT}/lib64/${CUDAToolkit_VERSION_MAJOR}
        ${CUTENSORNET_ROOT}/lib/${CUDAToolkit_VERSION_MAJOR}
        ${CUDA_QUANTUM_PATH}/lib
        $ENV{CONDA_PREFIX}/lib
        $ENV{CONDA_PREFIX}/lib/python*/site-packages/cuquantum/lib
    REQUIRED
)

# Find cuTensorNet header
find_file(CUTENSORNET_INC
    NAMES cutensornet.h
    HINTS 
        ${CUTENSORNET_ROOT}/include      
        ${CUDA_QUANTUM_PATH}/include
        $ENV{CONDA_PREFIX}/include
        $ENV{CONDA_PREFIX}/lib/python*/site-packages/cuquantum/include
        /usr/include
        ENV CPATH
    REQUIRED
)

# Validate dependencies
if(NOT CUTENSOR_LIB)
    message(FATAL_ERROR "Unable to find cuTensor installation. Please install with: conda install cutensor -c nvidia")
endif() 
message(STATUS "CUTENSOR_LIB: ${CUTENSOR_LIB}")

if(NOT CUTENSORNET_LIB OR NOT CUTENSORNET_INC)
    message(FATAL_ERROR "Unable to find cuTensorNet installation. Please install with: conda install cuquantum -c nvidia")
endif()
message(STATUS "CUTENSORNET_LIB: ${CUTENSORNET_LIB}")
message(STATUS "CUTENSORNET_INC: ${CUTENSORNET_INC}")

# Get include and lib directories
get_filename_component(CUTENSORNET_INCLUDE_DIR ${CUTENSORNET_INC} DIRECTORY)
get_filename_component(CUTENSORNET_LIB_DIR ${CUTENSORNET_LIB} DIRECTORY)
get_filename_component(CUTENSOR_LIB_DIR ${CUTENSOR_LIB} DIRECTORY)

# Set RPATH for runtime linking
set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_RPATH};${CUTENSORNET_LIB_DIR};${CUTENSOR_LIB_DIR}")

# Determine cutensornet version
file(READ "${CUTENSORNET_INC}" cutensornet_header)
string(REGEX MATCH "CUTENSORNET_MAJOR ([0-9]*)" _ ${cutensornet_header})
set(CUTENSORNET_MAJOR ${CMAKE_MATCH_1})

string(REGEX MATCH "CUTENSORNET_MINOR ([0-9]*)" _ ${cutensornet_header})
set(CUTENSORNET_MINOR ${CMAKE_MATCH_1})

string(REGEX MATCH "CUTENSORNET_PATCH ([0-9]*)" _ ${cutensornet_header})
set(CUTENSORNET_PATCH ${CMAKE_MATCH_1})

set(CUTENSORNET_VERSION ${CUTENSORNET_MAJOR}.${CUTENSORNET_MINOR}.${CUTENSORNET_PATCH})
message(STATUS "Found cutensornet version: ${CUTENSORNET_VERSION}")

if (${CUTENSORNET_VERSION} VERSION_LESS "2.7")
    message(FATAL_ERROR "cutensornet version ${CUTENSORNET_VERSION} is too old. Requires v2.7.0+.")
endif()

# Define source directories (relative to current project)
set(CUTENSORNET_SRC_DIR "${CMAKE_SOURCE_DIR}/src")

# Common sources for tensornet backends
set(TENSORNET_SOURCES
    ${CUTENSORNET_SRC_DIR}/tensornet_utils.cpp
    ${CUTENSORNET_SRC_DIR}/mpi_support.cpp
)

message(STATUS "")
message(STATUS "=== FormoTensor Build Configuration ===")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "NVQIR found: ${NVQIR_FOUND}")
message(STATUS "CuTensorNet version: ${CUTENSORNET_VERSION}")
message(STATUS "Targets to build:")

# Helper function to write target config (mimics CUDA-Q's internal function)
function(nvqir_write_target_config BackendName GPURequirements FilePath)
    # Convert hyphens to underscores for the backend identifier
    string(REPLACE "-" "_" BackendIdentifier ${BackendName})
    
    # Write YAML content line by line to avoid formatting issues
    file(WRITE ${FilePath} "name: ${BackendName}\n")
    file(APPEND ${FilePath} "description: \"FormoTensor ${BackendName} backend\"\n")
    file(APPEND ${FilePath} "gpu-requirements: ${GPURequirements}\n")
    file(APPEND ${FilePath} "config:\n")
    file(APPEND ${FilePath} "  nvqir-simulation-backend: ${BackendIdentifier}\n")
endfunction()

# Add the formotensor backend (FP64)
message(STATUS "  - nvqir-formotensor (FP64)")
add_library(nvqir-formotensor SHARED
    ${TENSORNET_SOURCES}
    ${CUTENSORNET_SRC_DIR}/simulator_tensornet_fp64_register.cpp
)

target_include_directories(nvqir-formotensor PRIVATE
    ${CUTENSORNET_SRC_DIR}
    ${CUDAToolkit_INCLUDE_DIRS}
    ${CUTENSORNET_INCLUDE_DIR}
    ${EIGEN3_INCLUDE_DIR}
)

target_link_libraries(nvqir-formotensor PRIVATE
    nvqir::nvqir
    ${CUTENSORNET_LIB}
    ${CUTENSOR_LIB}
    CUDA::cudart_static
)

target_compile_definitions(nvqir-formotensor PRIVATE
    CUDAQ_SIMULATION_SCALAR_FP64
)

install(TARGETS nvqir-formotensor DESTINATION ${NVQIR_SIMULATOR_PLUGIN_PATH})
nvqir_write_target_config(formotensor TRUE ${CMAKE_BINARY_DIR}/formotensor.yml)
install(FILES ${CMAKE_BINARY_DIR}/formotensor.yml DESTINATION ${NVQIR_SIMULATOR_CONFIG_PATH})

# Add the formotensor-mps backend (FP64)
message(STATUS "  - nvqir-formotensor-mps (FP64)")
add_library(nvqir-formotensor-mps SHARED
    ${TENSORNET_SOURCES}
    ${CUTENSORNET_SRC_DIR}/simulator_mps_fp64_register.cpp
)

target_include_directories(nvqir-formotensor-mps PRIVATE
    ${CUTENSORNET_SRC_DIR}
    ${CUDAToolkit_INCLUDE_DIRS}
    ${CUTENSORNET_INCLUDE_DIR}
    ${EIGEN3_INCLUDE_DIR}
)

target_link_libraries(nvqir-formotensor-mps PRIVATE
    nvqir::nvqir
    ${CUTENSORNET_LIB}
    ${CUTENSOR_LIB}
    CUDA::cudart_static
)

target_compile_definitions(nvqir-formotensor-mps PRIVATE
    CUDAQ_SIMULATION_SCALAR_FP64
)

install(TARGETS nvqir-formotensor-mps DESTINATION ${NVQIR_SIMULATOR_PLUGIN_PATH})
nvqir_write_target_config(formotensor-mps TRUE ${CMAKE_BINARY_DIR}/formotensor-mps.yml)
install(FILES ${CMAKE_BINARY_DIR}/formotensor-mps.yml DESTINATION ${NVQIR_SIMULATOR_CONFIG_PATH})

# Add the formotensor-fp32 backend (FP32)
message(STATUS "  - nvqir-formotensor-fp32 (FP32)")
add_library(nvqir-formotensor-fp32 SHARED
    ${TENSORNET_SOURCES}
    ${CUTENSORNET_SRC_DIR}/simulator_tensornet_fp32_register.cpp
)

target_include_directories(nvqir-formotensor-fp32 PRIVATE
    ${CUTENSORNET_SRC_DIR}
    ${CUDAToolkit_INCLUDE_DIRS}
    ${CUTENSORNET_INCLUDE_DIR}
    ${EIGEN3_INCLUDE_DIR}
)

target_link_libraries(nvqir-formotensor-fp32 PRIVATE
    nvqir::nvqir
    ${CUTENSORNET_LIB}
    ${CUTENSOR_LIB}
    CUDA::cudart_static
)

target_compile_definitions(nvqir-formotensor-fp32 PRIVATE
    CUDAQ_SIMULATION_SCALAR_FP32
)

install(TARGETS nvqir-formotensor-fp32 DESTINATION ${NVQIR_SIMULATOR_PLUGIN_PATH})
nvqir_write_target_config(formotensor-fp32 TRUE ${CMAKE_BINARY_DIR}/formotensor-fp32.yml)
install(FILES ${CMAKE_BINARY_DIR}/formotensor-fp32.yml DESTINATION ${NVQIR_SIMULATOR_CONFIG_PATH})

# Add the formotensor-mps-fp32 backend (FP32)
message(STATUS "  - nvqir-formotensor-mps-fp32 (FP32)")
add_library(nvqir-formotensor-mps-fp32 SHARED
    ${TENSORNET_SOURCES}
    ${CUTENSORNET_SRC_DIR}/simulator_mps_fp32_register.cpp
)

target_include_directories(nvqir-formotensor-mps-fp32 PRIVATE
    ${CUTENSORNET_SRC_DIR}
    ${CUDAToolkit_INCLUDE_DIRS}
    ${CUTENSORNET_INCLUDE_DIR}
    ${EIGEN3_INCLUDE_DIR}
)

target_link_libraries(nvqir-formotensor-mps-fp32 PRIVATE
    nvqir::nvqir
    ${CUTENSORNET_LIB}
    ${CUTENSOR_LIB}
    CUDA::cudart_static
)

target_compile_definitions(nvqir-formotensor-mps-fp32 PRIVATE
    CUDAQ_SIMULATION_SCALAR_FP32
)

install(TARGETS nvqir-formotensor-mps-fp32 DESTINATION ${NVQIR_SIMULATOR_PLUGIN_PATH})
nvqir_write_target_config(formotensor-mps-fp32 TRUE ${CMAKE_BINARY_DIR}/formotensor-mps-fp32.yml)
install(FILES ${CMAKE_BINARY_DIR}/formotensor-mps-fp32.yml DESTINATION ${NVQIR_SIMULATOR_CONFIG_PATH})

message(STATUS "==================================================")
message(STATUS "")
