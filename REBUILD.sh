#!/bin/bash
# Quick rebuild script for formotensor_bridge

set -e  # Exit on error

echo "=========================================="
echo "Rebuilding formotensor_bridge"
echo "=========================================="

cd /work/u4876763/FormoTensor/build

echo ""
echo "[1/3] Cleaning old Python module..."
rm -f python/formotensor_bridge*.so

echo ""
echo "[2/3] Rebuilding..."
ninja formotensor_bridge

echo ""
echo "[3/3] Installing..."
ninja install

echo ""
echo "=========================================="
echo "✓ Rebuild complete!"
echo "=========================================="
echo ""
echo "Run tests with:"
echo "  python test_bridge_simple.py              # Quick functionality test"
echo "  python test_bridge_functionality_fixed.py # Full test suite (RECOMMENDED)"
echo "  python test_state_api.py                  # State API exploration"
echo ""

