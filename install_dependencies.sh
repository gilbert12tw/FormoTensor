#!/bin/bash

# FormoTensor - Dependencies Installation Script
# This script creates a conda environment and installs all required dependencies

set -e  # Exit on any error

echo "======================================================"
echo "      FormoTensor Dependencies Installation"
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

# Environment name
ENV_NAME="formotensor-env"

# Function to create and setup conda environment
setup_conda_env() {
    echo ""
    echo "🏗️  Setting up conda environment..."
    
    # Check if environment already exists
    if conda env list | grep -q "^$ENV_NAME"; then
        echo "⚠️  Environment '$ENV_NAME' already exists."
        read -p "Would you like to remove it and create fresh? (Y/n): " choice
        if [[ ! "$choice" =~ ^[Nn]$ ]]; then
            echo "🗑️  Removing existing environment..."
            conda env remove -n "$ENV_NAME" -y
        else
            echo "❌ Please manually remove the environment or choose a different name"
            exit 1
        fi
    fi
    
    echo "🆕 Creating new conda environment '$ENV_NAME'..."
    conda create -n "$ENV_NAME" python=3.11 -y
    
    echo "✅ Environment '$ENV_NAME' created successfully!"
    
    # Activate environment
    echo "🔄 Activating environment..."
    eval "$(conda shell.bash hook)"
    conda activate "$ENV_NAME"
    
    echo "✅ Environment activated: $(conda info --envs | grep '*')"
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

# Function to configure conda channels
configure_conda_channels() {
    echo "⚙️  Configuring conda channels..."
    conda config --add channels nvidia
    conda config --add channels conda-forge
    conda config --set channel_priority strict
    echo "✅ Conda channels configured"
}

# Function to install CUDA package with fallback
install_cuda_package() {
    local package_name=$1
    local version=${2:-"12.4"}
    local channel=${3:-"nvidia"}
    
    echo "Installing $package_name..."
    
    # Try with specific version first
    if conda install -y -c "$channel" "$package_name=$version" 2>/dev/null; then
        echo "✅ Successfully installed $package_name=$version"
        return 0
    fi
    
    # Try without version if specific version fails
    if conda install -y -c "$channel" "$package_name" 2>/dev/null; then
        echo "✅ Successfully installed $package_name (latest available)"
        return 0
    fi
    
    echo "⚠️  $package_name not available, skipping..."
    return 1
}

# Setup environment first
setup_conda_env

# Configure channels
configure_conda_channels

echo ""
echo "📦 Installing dependencies..."
echo ""

# 1. Install GCC (C++ compiler with C++20 support)
echo "1️⃣  Installing GCC 11+ for C++20 support..."
install_package "gcc=11 gxx=11" "conda-forge"

# 2. Install CUDA toolkit (pin everything to 12.9 in ONE transaction)
echo ""
echo "2️⃣  Installing CUDA toolkit 12.9 (pinned critical subpackages)..."
# Pin critical CUDA components to 12.9.* so nvcc matches libcudadevrt
install_package "cuda-toolkit=12.9.* cuda-compiler=12.9.* cuda-nvcc=12.9.* cuda-cudart=12.9.* cuda-cudart-dev=12.9.* cuda-nvrtc=12.9.* cuda-nvrtc-dev=12.9.* cuda-libraries=12.9.* cuda-libraries-dev=12.9.*" "nvidia"

# Validate no mismatched CUDA packages remain (reject anything not 12.9)
echo "🔍 Validating CUDA package versions..."
MISMATCHED=$(conda list | awk '/^cuda-/{ if ($2 !~ /^12\.9(\.|$)/) print $1"=="$2 }')
if [[ -n "$MISMATCHED" ]]; then
    echo "❌ Found mismatched CUDA packages (not 12.9):"
    echo "$MISMATCHED"
    echo "💡 Tip: A clean re-run usually fixes this: conda env remove -n $ENV_NAME && ./install_dependencies.sh"
    exit 1
fi

# 3. Install Eigen3 (linear algebra library)
echo ""
echo "3️⃣  Installing Eigen3..."
install_package "eigen" "conda-forge"

# 4. Install cuTensor (CUDA 12 variant)
echo ""
echo "4️⃣  Installing cuTensor..."
install_package "cutensor cutensor-cuda-12" "nvidia"

# 5. Install cuQuantum (CUDA 12 variant, includes cuTensorNet)
echo ""
echo "5️⃣  Installing cuQuantum (cuTensorNet)..."
install_package "cuquantum cuquantum-cuda-12" "nvidia"

# 6. Install CUDA-Q (via pip - not available in conda)
echo ""
echo "6️⃣  Installing CUDA-Q..."
echo "Installing CUDA-Q 0.12.* via pip (conda not available)..."
install_pip_package "cudaq>=0.12.0,<0.13.0"

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
CONDA_ENV_PATH=$(conda info --base)/envs/$ENV_NAME

# Find CUDA-Q installation path (pip installation)
echo "🔍 Detecting CUDA-Q installation path..."

# Check for pip installation
PIP_CUDAQ_PATH=$(python -c "import cudaq; import os; print(os.path.dirname(cudaq.__file__))" 2>/dev/null)
if [[ -n "$PIP_CUDAQ_PATH" ]]; then
    # CUDA-Q installed via pip
    CUDAQ_PYTHON_PATH=$(dirname "$PIP_CUDAQ_PATH")
    echo "✅ Found CUDA-Q via pip at: $CUDAQ_PYTHON_PATH"
else
    # Check for conda installation as fallback
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

# Create environment setup script (ensures clean PATH/LD_LIBRARY_PATH)
ENV_SCRIPT="setup_environment.sh"
cat > "$ENV_SCRIPT" << EOF
#!/bin/bash
# FormoTensor Environment Setup
# Source this script before building: source setup_environment.sh

# Ensure we're in the correct conda environment
if [[ "\$CONDA_DEFAULT_ENV" != "$ENV_NAME" ]]; then
    echo "⚠️  Please activate the environment first: conda activate $ENV_NAME"
    return 1
fi

# Get current conda environment path
CONDA_ENV_PATH=\$(conda info --base)/envs/$ENV_NAME

# CUDA-Q paths
export CUDA_QUANTUM_PATH="$CUDAQ_PYTHON_PATH"

# CUDA toolkit paths
export CUDA_HOME="\$CONDA_ENV_PATH"
export CUDA_ROOT="\$CONDA_ENV_PATH"
export CUDA_PATH="\$CONDA_ENV_PATH"

# cuTensor and cuTensorNet paths
export CUTENSOR_ROOT="\$CONDA_ENV_PATH"
export CUTENSORNET_ROOT="\$CONDA_ENV_PATH"

# Clean PATH/LD_LIBRARY_PATH from other conda CUDA envs
LD_LIBRARY_PATH=\$(echo "\$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v "/envs/" | tr '\n' ':' | sed 's/:$//')
PATH=\$(echo "\$PATH" | tr ':' '\n' | grep -v "/envs/" | tr '\n' ':' | sed 's/:$//')

# Ensure our env comes first
export LD_LIBRARY_PATH="\$CONDA_ENV_PATH/lib:\$LD_LIBRARY_PATH"
export PATH="\$CONDA_ENV_PATH/bin:\$PATH"

echo "Environment variables set:"
echo "  CUDA_QUANTUM_PATH=\$CUDA_QUANTUM_PATH"
echo "  CUDA_HOME=\$CUDA_HOME"
echo "  CUTENSOR_ROOT=\$CUTENSOR_ROOT"  
echo "  CUTENSORNET_ROOT=\$CUTENSORNET_ROOT"
echo "  LD_LIBRARY_PATH=\$LD_LIBRARY_PATH"

# Verify CUDA installation
if command -v nvcc &> /dev/null; then
    NVCC_VERSION=\$(nvcc --version | grep release | sed 's/.*release \\([0-9]\\+\\.[0-9]\\+\\).*/\\1/')
    echo "✅ CUDA compiler: \$(nvcc --version | grep release)"
    if [[ "\$NVCC_VERSION" == "12.9" || "\$NVCC_VERSION" == "12.9."* ]]; then
        echo "✅ CUDA 12.9 version confirmed"
    else
        echo "⚠️  Warning: Expected CUDA 12.9, found \$NVCC_VERSION"
    fi
else
    echo "⚠️  CUDA compiler (nvcc) not found in PATH"
fi

# Verify cuTensor installation
echo "🔍 Verifying cuTensor installation..."
if find "\$CONDA_ENV_PATH" -name "*cutensor*" -type f 2>/dev/null | head -1 | grep -q cutensor; then
    echo "✅ cuTensor found"
else
    echo "⚠️  cuTensor not found"
fi

# Verify cuQuantum installation
echo "🔍 Verifying cuQuantum installation..."
if find "\$CONDA_ENV_PATH" -name "*cuquantum*" -o -name "*cutensornet*" -type f 2>/dev/null | head -1 | grep -q .; then
    echo "✅ cuQuantum/cuTensorNet found"
else
    echo "⚠️  cuQuantum/cuTensorNet not found"
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
echo "   For this session:"
echo "     1. Environment is already active, run: source $ENV_SCRIPT"
echo "     2. Build the project: ./build.sh"
echo "     3. Test the installation: python test_formotensor.py"
echo ""
echo "   For future sessions:"
echo "     1. Activate environment: conda activate $ENV_NAME"
echo "     2. Source environment: source $ENV_SCRIPT"
echo "     3. Build/run your project"
echo ""
echo "💡 Environment '$ENV_NAME' has been created with all dependencies."
echo "   All CUDA components use version 12.9 to ensure compatibility."
echo ""

# Verify final installation
echo "🔍 Final verification:"
echo "  Environment: $(conda info --envs | grep '*' | awk '{print $1}')"
echo "  Python: $(python --version)"
echo "  CUDA: $(nvcc --version 2>/dev/null | grep release || echo 'Not found')"
if python -c "import cudaq" 2>/dev/null; then
    echo "  CUDA-Q: ✅ Ready"
else
    echo "  CUDA-Q: ❌ Import failed"
fi
echo ""
