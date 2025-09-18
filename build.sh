#!/bin/bash

# FormoTensor Build Script

set -e  # Exit on any error

echo "========================================"
echo "      FormoTensor Build"
echo "========================================"
echo ""

# Check required environment variables
check_env_var() {
    local var_name=$1
    if [[ -z "${!var_name}" ]]; then
        echo "❌ Environment variable $var_name is not set"
        echo "Please run: source setup_environment.sh"
        exit 1
    fi
    echo "✅ $var_name = ${!var_name}"
}

echo "🔍 Checking environment variables..."
check_env_var "CUDA_QUANTUM_PATH"
check_env_var "CUDA_HOME"
check_env_var "CUTENSOR_ROOT"
check_env_var "CUTENSORNET_ROOT"

# Verify CUDA-Q installation method
echo ""
echo "🔍 Verifying CUDA-Q installation..."
if python -c "import cudaq; print(f'CUDA-Q version: {cudaq.__version__ if hasattr(cudaq, \"__version__\") else \"unknown\"}')" 2>/dev/null; then
    echo "✅ CUDA-Q is working correctly"
else
    echo "❌ CUDA-Q import failed"
    echo "Please ensure CUDA-Q is properly installed via pip or conda"
    exit 1
fi

# Check if NVQIR is available
if [[ ! -d "$CUDA_QUANTUM_PATH/lib/cmake/nvqir" ]]; then
    echo "❌ NVQIR CMake files not found in $CUDA_QUANTUM_PATH/lib/cmake/nvqir"
    echo "Please verify your CUDA_QUANTUM_PATH is correct."
    exit 1
fi

echo "✅ NVQIR found at: $CUDA_QUANTUM_PATH/lib/cmake/nvqir"

# Check compiler version
echo ""
echo "🔍 Checking compiler..."
if command -v g++ &> /dev/null; then
    GCC_VERSION=$(g++ -dumpversion)
    echo "✅ Found GCC version: $GCC_VERSION"
    
    # Check if GCC supports C++20
    if [[ "$(printf '%s\n' "11.0" "$GCC_VERSION" | sort -V | head -n1)" == "11.0" ]]; then
        echo "✅ GCC $GCC_VERSION supports C++20"
    else
        echo "❌ GCC $GCC_VERSION does not fully support C++20"
        echo "Please install GCC 11+: conda install -c conda-forge gcc=11 gxx=11"
        exit 1
    fi
else
    echo "❌ GCC not found"
    echo "Please install GCC: conda install -c conda-forge gcc=11 gxx=11"
    exit 1
fi

# Create and clean build directory
BUILD_DIR="build"
echo ""
echo "🏗️  Preparing build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure with CMake
echo ""
echo "⚙️  Configuring with CMake..."
cmake .. -G Ninja \
    -DNVQIR_DIR="$CUDA_QUANTUM_PATH/lib/cmake/nvqir" \
    -DCMAKE_INSTALL_PREFIX="$CUDA_QUANTUM_PATH"

# Build
echo ""
echo "🔨 Building..."
ninja

# Install
echo ""
echo "📦 Installing..."
ninja install

echo ""
echo "========================================"
echo "✅ Build completed successfully!"
echo "========================================"
echo ""
echo "🎯 Installed backends:"
echo "   - nvqir-formotensor (FP64)"
echo "   - nvqir-formotensor-mps (FP64)" 
echo "   - nvqir-formotensor-fp32 (FP32)"
echo "   - nvqir-formotensor-mps-fp32 (FP32)"
echo ""
echo "🧪 Test the installation:"
echo "   python test_formotensor.py"
echo ""
