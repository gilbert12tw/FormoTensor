# FormoTensor

A standalone project for building and installing enhanced cuTensorNet simulation backends for CUDA-Q with additional functionality and optimizations.

## 📋 Prerequisites

### System Requirements
- Linux (tested on CentOS/RHEL 8+, Ubuntu 20.04+)
- NVIDIA GPU with CUDA capability 7.0+
- Conda or Miniconda/Miniforge

### Required Dependencies
All dependencies can be installed using conda/pip:

1. **GCC 11+** - C++ compiler with C++20 support
2. **CUDA Toolkit 12.x** - NVIDIA CUDA development kit
3. **Eigen 3.4+** - C++ linear algebra library
4. **cuTensor** - NVIDIA tensor linear algebra library
5. **cuQuantum (cuTensorNet)** - NVIDIA quantum circuit simulation library
6. **CUDA-Q** - NVIDIA quantum computing platform (installed via pip)
7. **CMake 3.24+** - Build system generator
8. **Ninja** - Fast build system

### GPU Requirements
- NVIDIA GPU with compute capability 7.0+
- CUDA 12.x or compatible version

## 🚀 Quick Start

### Step 1: Install Dependencies

Run the automated installation script:

```bash
# Make the script executable
chmod +x install_dependencies.sh

# Install all dependencies
./install_dependencies.sh
```

This will:
- Check for conda availability
- Install all required packages using conda and pip
- Create an environment setup script

### Step 2: Set Environment Variables

```bash
# Source the auto-generated environment script
source setup_environment.sh
```

This sets:
- `CUDA_QUANTUM_PATH`: Path to CUDA-Q installation
- `CUTENSOR_ROOT`: Path to cuTensor installation  
- `CUTENSORNET_ROOT`: Path to cuTensorNet installation

### Step 3: Build the Project

```bash
# Make the build script executable
chmod +x build.sh

# Build and install
./build.sh
```

### Step 4: Test the Installation

```bash
# Run the comprehensive test suite
python test_formotensor.py
```

Or manually check available backends:

```bash
# Check if backends are loaded
python -c "
import cudaq
print('Available targets:')
for target in cudaq.get_targets():
    if 'formotensor' in target.name:
        print(f'  ✓ {target.name}')
"
```

## 🔧 Manual Installation

If you prefer to install dependencies manually:

### Create Conda Environment (Optional but Recommended)

```bash
conda create -n formotensor-env python=3.11
conda activate formotensor-env
```

### Install Dependencies

```bash
# Install compiler and build tools
conda install -c conda-forge gcc=11 gxx=11 cmake ninja

# Install CUDA 12.x
conda install -c nvidia cuda-toolkit=12.4 cuda-nvcc=12.4 cuda-cudart-dev=12.4

# Install NVIDIA quantum packages
conda install -c nvidia cutensor cuquantum

# Install CUDA-Q via pip (recommended)
pip install cudaq

# Install other dependencies  
conda install -c conda-forge eigen
pip install numpy
```

### Set Environment Variables

```bash
# For pip-installed CUDA-Q, the script will auto-detect paths
export CUDA_QUANTUM_PATH="$(python -c 'import cudaq, os; print(os.path.dirname(os.path.dirname(cudaq.__file__)))')"
export CUDA_HOME="/path/to/conda/envs/formotensor-env"
export CUTENSOR_ROOT="/path/to/conda/envs/formotensor-env"
export CUTENSORNET_ROOT="/path/to/conda/envs/formotensor-env"
export LD_LIBRARY_PATH="/path/to/conda/envs/formotensor-env/lib:$LD_LIBRARY_PATH"
```

### Build Manually

```bash
mkdir build && cd build
cmake .. -G Ninja \
    -DNVQIR_DIR="$CUDA_QUANTUM_PATH/lib/cmake/nvqir" \
    -DCMAKE_INSTALL_PREFIX="$CUDA_QUANTUM_PATH"
ninja
ninja install
```

## 📦 Installed Backends

After successful installation, the following backends will be available in CUDA-Q:

| Backend Name | Precision | Description |
|--------------|-----------|-------------|
| `formotensor` | FP64 | Enhanced tensor network simulation (double precision) |
| `formotensor-mps` | FP64 | Enhanced Matrix Product State simulation (double precision) |
| `formotensor-fp32` | FP32 | Enhanced tensor network simulation (single precision) |
| `formotensor-mps-fp32` | FP32 | Enhanced Matrix Product State simulation (single precision) |

## 🧪 Usage Example

```python
import cudaq

# Use the formotensor backend
cudaq.set_target("formotensor")

@cudaq.kernel
def quantum_circuit():
    qubits = cudaq.qvector(4)
    h(qubits[0])
    for i in range(3):
        cx(qubits[i], qubits[i+1])
    mz(qubits)

# Run the circuit
result = cudaq.sample(quantum_circuit)
print(f"Results: {result}")
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Environment Variables Not Set
```bash
# Error: CUDA_QUANTUM_PATH environment variable is not set
source setup_environment.sh
```

#### 2. GCC Version Too Old
```bash
# Error: GCC does not fully support C++20
conda install -c conda-forge gcc=11 gxx=11
conda deactivate && conda activate formotensor-env
```

#### 3. NVQIR Not Found
```bash
# Error: NVQIR CMake files not found
# Ensure CUDA-Q is properly installed
conda install -c nvidia cudaq
```

#### 4. cuTensor/cuTensorNet Not Found
```bash
# Error: Unable to find cutensor/cutensornet installation
conda install -c nvidia cutensor cuquantum
```

#### 5. Eigen SVD Template Error
This is already fixed in the source code. If you encounter:
```
error: wrong number of template arguments (2, should be 1)
```
The project automatically handles Eigen 3.4+ API changes.

### Verify Installation

```bash
# Or check manually
python -c "
import cudaq
print('FormoTensor backends:')
for target in cudaq.get_targets():
    if 'formotensor' in target.name:
        print(f'  ✓ {target.name}')
"
```

## 📁 Project Structure

```
FormoTensor/
├── CMakeLists.txt              # Main CMake configuration
├── install_dependencies.sh     # Automated dependency installer
├── setup_environment.sh        # Environment variables (auto-generated)
├── build.sh                   # Build script
├── test_formotensor.py        # Comprehensive test suite
├── README.md                  # This file
├── src/                       # Enhanced source code
│   ├── tensornet_utils.cpp
│   ├── mpi_support.cpp
│   ├── simulator_*_register.cpp
│   ├── simulator_tensornet.h
│   ├── simulator_mps.h
│   └── ...
└── build/                     # Build artifacts (generated)
    ├── *.so                   # Compiled backend libraries
    └── *.yml                  # Backend configuration files
```

## 🤝 Contributing

FormoTensor is based on cuTensorNet backends from CUDA-Q, enhanced with additional functionality and optimizations.

- Original CUDA-Q project: https://github.com/NVIDIA/cuda-quantum
- For issues related to CUDA-Q core functionality, please report to the main CUDA-Q repository
- For issues specific to FormoTensor enhancements, create an issue in this repository

### What's Enhanced in FormoTensor
- Optimized memory management for large quantum circuits
- Enhanced MPI support for distributed simulations
- Additional debugging and profiling tools
- Custom gate implementations and optimizations

## 📄 License

This project contains code extracted from CUDA-Q and maintains the same licensing terms as the original project.

## 🔗 References

- [CUDA-Q Documentation](https://nvidia.github.io/cuda-quantum/)
- [cuQuantum Documentation](https://docs.nvidia.com/cuda/cuquantum/)
- [cuTensorNet Documentation](https://docs.nvidia.com/cuda/cuquantum/cutn/index.html)
