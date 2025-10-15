#!/usr/bin/env python3
"""
Simple test for the updated formotensor_bridge
Tests the TensorNetworkHelper API with cudaq.State objects
"""

import cudaq
import formotensor_bridge as ftb

print("=" * 70)
print("FormoTensor Bridge - Simple Functionality Test")
print("=" * 70)
print(f"Bridge version: {ftb.__version__}")

# Define a simple circuit
@cudaq.kernel
def bell_state():
    """2-qubit Bell state"""
    q = cudaq.qvector(2)
    h(q[0])
    cx(q[0], q[1])

# Set backend
print("\n[1] Setting backend to tensornet...")
cudaq.set_target("tensornet")
print("✓ Backend set")

# Get state
print("\n[2] Executing circuit and getting state...")
try:
    state = cudaq.get_state(bell_state)
    print(f"✓ Got state object: {type(state).__name__}")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test bridge API
print("\n[3] Testing bridge API...")

# Test 3.1: Get number of qubits
print("\n  [3.1] Getting number of qubits...")
try:
    num_qubits = ftb.TensorNetworkHelper.get_num_qubits(state)
    print(f"  ✓ Number of qubits: {num_qubits}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 3.2: Check if state has tensors
print("\n  [3.2] Checking if state has tensor methods...")
try:
    has_tensors = ftb.TensorNetworkHelper.has_tensors(state)
    print(f"  ✓ Has tensor methods: {has_tensors}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    has_tensors = False

# Test 3.3: Get all tensors info
if has_tensors:
    print("\n  [3.3] Getting all tensors info...")
    try:
        tensors_info = ftb.TensorNetworkHelper.get_all_tensors_info(state)
        print(f"  ✓ Found {len(tensors_info)} tensors")
        for i, info in enumerate(tensors_info):
            print(f"    Tensor {i}: {info}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        
    # Test 3.4: Get specific tensor info
    print("\n  [3.4] Getting specific tensor info...")
    try:
        info = ftb.TensorNetworkHelper.get_tensor_info(state, 0)
        print(f"  ✓ Tensor 0 info: {info}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3.5: Extract tensor data
    print("\n  [3.5] Extracting tensor data...")
    try:
        tensor_data = ftb.TensorNetworkHelper.extract_tensor_data(state, 0)
        print(f"  ✓ Extracted tensor shape: {tensor_data.shape}")
        print(f"    Tensor dtype: {tensor_data.dtype}")
        print(f"    First 4 elements: {tensor_data.flat[:4]}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n  [3.3-3.5] Skipped (no tensor methods available)")

# Test 4: Explore state object directly
print("\n[4] Exploring state object directly...")
print(f"  State methods: {[m for m in dir(state) if not m.startswith('_')]}")

# Try getTensor directly
print("\n  [4.1] Trying getTensor(0) directly...")
try:
    tensor = state.getTensor(0)
    print(f"  ✓ Got tensor object: {type(tensor)}")
    print(f"    Tensor attributes: {[a for a in dir(tensor) if not a.startswith('_')]}")
    
    # Try to access extents
    if hasattr(tensor, 'extents'):
        print(f"    Tensor extents: {tensor.extents}")
    
    # Try to access data
    if hasattr(tensor, 'data'):
        print(f"    Tensor has 'data' attribute")
        
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()

# Try getTensors directly
print("\n  [4.2] Trying getTensors() directly...")
try:
    tensors = state.getTensors()
    print(f"  ✓ Got tensors object: {type(tensors)}")
    
    if hasattr(tensors, '__len__'):
        print(f"    Number of tensors: {len(tensors)}")
    
    if hasattr(tensors, '__iter__'):
        print(f"    Tensors are iterable")
        for i, t in enumerate(tensors):
            print(f"      Tensor {i}: {type(t)}")
            if i >= 2:  # Only show first 3
                print(f"      ...")
                break
        
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print("""
Key Findings:
- Bridge can now work with cudaq.State objects ✓
- We need to understand the getTensor/getTensors API structure
- Next: trace the exact structure of Tensor objects returned
""")
print("=" * 70)

