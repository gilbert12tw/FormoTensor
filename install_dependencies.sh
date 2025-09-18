#!/bin/bash

# CuTensorNet Standalone - Dependencies Installation Script
# This script installs all required dependencies using conda and pip

set -e  # Exit on any error

echo "======================================================"
echo "   CuTensorNet Standalone Dependencies Installation"
echo "======================================================"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Conda is not installed or not in PATH"
    echo "Please install Miniforge or Anaconda first:"
    echo "  https://github.com/conda-forge/miniforge"
    exit 1
fi

echo "✅ Found conda: $(conda --version)"

# Function to check if we're in a conda environment
check_conda_env() {
    if [[ -z "$CONDA_DEFAULT_ENV" ]]; then
        echo "⚠️  Warning: No conda environment is currently active"
        echo "It's recommended to create and activate a dedicated environment:"
        echo "  conda create -n cutensornet-env python=3.11"
        echo "  conda activate cutensornet-env"
        echo ""
        read -p "Continue with base environment? (y/N): " choice
        if [[ ! "$choice" =~ ^[Yy]$ ]]; then
            echo "Exiting..."
            exit 1
        fi
    else
        echo "✅ Using conda environment: $CONDA_DEFAULT_ENV"
    fi
}

# Install function with error checking
install_package() {
    local package=$1
    local channel=${2:-""}
    local cmd="conda install -y $package"
    
    if [[ -n "$channel" ]]; then
        cmd="conda install -y -c $channel $package"
    fi
    
    echo "Installing $package..."
    if eval "$cmd"; then
        echo "✅ Successfully installed $package"
    else
        echo "❌ Failed to install $package"
        exit 1
    fi
}

# Install pip package with error checking
install_pip_package() {
    local package=$1
    echo "Installing $package via pip..."
    if pip install "$package"; then
        echo "✅ Successfully installed $package"
    else
        echo "❌ Failed to install $package"
        exit 1
    fi
}

check_conda_env

echo ""
echo "📦 Installing dependencies..."
echo ""

# 1. Install GCC (C++ compiler with C++20 support)
echo "1️⃣  Installing GCC 11+ for C++20 support..."
install_package "gcc=11 gxx=11" "conda-forge"

# 2. Install CUDA toolkit (12.x for H100 GPU support)
echo ""
echo "2️⃣  Installing CUDA toolkit 12.x for H100 GPU..."
install_package "cuda-toolkit=12.4" "nvidia"
install_package "cuda-nvcc=12.4" "nvidia"
install_package "cuda-cudart-dev=12.4" "nvidia"

# 3. Install Eigen3 (linear algebra library)
echo ""
echo "3️⃣  Installing Eigen3..."
install_package "eigen" "conda-forge"

# 4. Install cuTensor
echo ""
echo "4️⃣  Installing cuTensor..."
install_package "cutensor" "nvidia"

# 5. Install cuQuantum (includes cuTensorNet)
echo ""
echo "5️⃣  Installing cuQuantum (cuTensorNet)..."
install_package "cuquantum" "nvidia"

# 6. Install CUDA-Q via pip (recommended method)
echo ""
echo "6️⃣  Installing CUDA-Q via pip..."
echo "Installing CUDA-Q via pip..."
if pip install cudaq; then
    echo "✅ Successfully installed CUDA-Q via pip"
else
    echo "❌ Failed to install CUDA-Q via pip"
    echo "Falling back to conda installation..."
    install_package "cudaq" "nvidia"
fi

# 7. Install CMake and Ninja (build tools)
echo ""
echo "7️⃣  Installing build tools..."
install_package "cmake ninja" "conda-forge"

# 8. Install Python packages (for testing)
echo ""
echo "8️⃣  Installing Python testing packages..."
install_pip_package "numpy"

echo ""
echo "✅ All dependencies installed successfully!"
echo ""

# Set environment variables
echo "🔧 Setting up environment variables..."
echo ""

# Get conda environment path
CONDA_ENV_PATH=$(conda info --base)/envs/$CONDA_DEFAULT_ENV
if [[ "$CONDA_DEFAULT_ENV" == "base" ]]; then
    CONDA_ENV_PATH=$(conda info --base)
fi

# Find CUDA-Q installation path (pip or conda)
echo "🔍 Detecting CUDA-Q installation method..."

# First check for pip installation
PIP_CUDAQ_PATH=$(python -c "import cudaq; import os; print(os.path.dirname(cudaq.__file__))" 2>/dev/null)
if [[ -n "$PIP_CUDAQ_PATH" ]]; then
    # CUDA-Q installed via pip
    CUDAQ_PYTHON_PATH=$(dirname "$PIP_CUDAQ_PATH")
    echo "✅ Found CUDA-Q via pip at: $CUDAQ_PYTHON_PATH"
else
    # Check for conda installation
    CUDAQ_PYTHON_PATH=$(find "$CONDA_ENV_PATH" -path "*/site-packages" -name "cudaq*" -type d 2>/dev/null | head -1)
    if [[ -n "$CUDAQ_PYTHON_PATH" ]]; then
        CUDAQ_PYTHON_PATH=$(dirname "$CUDAQ_PYTHON_PATH")
        echo "✅ Found CUDA-Q via conda at: $CUDAQ_PYTHON_PATH"
    else
        # Fallback to default path
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        CUDAQ_PYTHON_PATH="$CONDA_ENV_PATH/lib/python$PYTHON_VERSION/site-packages"
        echo "⚠️  Could not find exact CUDA-Q path, using default: $CUDAQ_PYTHON_PATH"
    fi
fi

# Verify CUDA-Q is working
if python -c "import cudaq" 2>/dev/null; then
    echo "✅ CUDA-Q import successful"
else
    echo "❌ CUDA-Q import failed - please check installation"
fi

# Create environment setup script
ENV_SCRIPT="setup_environment.sh"
cat > "$ENV_SCRIPT" << EOF
#!/bin/bash
# CuTensorNet Standalone Environment Setup
# Source this script before building: source setup_environment.sh

# CUDA-Q paths
export CUDA_QUANTUM_PATH="$CUDAQ_PYTHON_PATH"

# CUDA toolkit paths (for H100 GPU support)
export CUDA_HOME="$CONDA_ENV_PATH"
export CUDA_ROOT="$CONDA_ENV_PATH"
export CUDA_PATH="$CONDA_ENV_PATH"

# cuTensor and cuTensorNet paths
export CUTENSOR_ROOT="$CONDA_ENV_PATH"
export CUTENSORNET_ROOT="$CONDA_ENV_PATH"

# Additional CUDA library paths
export LD_LIBRARY_PATH="$CONDA_ENV_PATH/lib:\$LD_LIBRARY_PATH"

# Ensure CUDA tools are in PATH
export PATH="$CONDA_ENV_PATH/bin:\$PATH"

echo "Environment variables set for H100 GPU:"
echo "  CUDA_QUANTUM_PATH=\$CUDA_QUANTUM_PATH"
echo "  CUDA_HOME=\$CUDA_HOME"
echo "  CUTENSOR_ROOT=\$CUTENSOR_ROOT"  
echo "  CUTENSORNET_ROOT=\$CUTENSORNET_ROOT"
echo "  LD_LIBRARY_PATH=\$LD_LIBRARY_PATH"

# Verify CUDA installation
if command -v nvcc &> /dev/null; then
    echo "✅ CUDA compiler: \$(nvcc --version | grep release)"
else
    echo "⚠️  CUDA compiler (nvcc) not found in PATH"
fi

# Verify GPU
if command -v nvidia-smi &> /dev/null; then
    echo "🖥️  GPU info:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader,nounits | head -1
else
    echo "⚠️  nvidia-smi not found"
fi
EOF

chmod +x "$ENV_SCRIPT"

echo ""
echo "📝 Created environment setup script: $ENV_SCRIPT"
echo ""
echo "======================================================"
echo "✅ Installation completed successfully!"
echo "======================================================"
echo ""
echo "📌 Next steps:"
echo "   1. Source the environment: source $ENV_SCRIPT"
echo "   2. Build the project: ./build.sh"
echo "   3. Test the installation: python test_cutensornet.py"
echo ""
echo "💡 Note: You'll need to source the environment script"
echo "   every time you open a new terminal session."
echo ""
