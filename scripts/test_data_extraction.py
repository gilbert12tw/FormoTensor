#!/usr/bin/env python3
"""
Test script to debug tensor data extraction
Focus on understanding tensor.data() return type
"""

import cudaq
import formotensor_bridge as ftb
import numpy as np

print("=" * 70)
print("Tensor Data Extraction Debug Test")
print("=" * 70)

# Setup
cudaq.set_target("tensornet")

@cudaq.kernel
def simple_circuit():
    q = cudaq.qvector(1)
    h(q[0])

# Get state
print("\n[1] Getting state...")
state = cudaq.get_state(simple_circuit)
print("✓ State obtained")

# Test direct Python access
print("\n[2] Testing direct Python access...")
try:
    tensor = state.getTensor(0)
    print(f"✓ Tensor object: {type(tensor)}")
    print(f"  Extents: {tensor.extents}")
    print(f"  Elements: {tensor.get_num_elements()}")
    
    # Call data() and inspect
    print("\n[3] Inspecting tensor.data()...")
    data_result = tensor.data()
    print(f"✓ data() returned: {type(data_result)}")
    print(f"  Type name: {type(data_result).__name__}")
    print(f"  Value: {data_result}")
    
    # Check if it's an integer
    if isinstance(data_result, int):
        print(f"  → It's an integer (pointer address)")
        print(f"  → Hex: {hex(data_result)}")
        print(f"  → This should work with our bridge")
    else:
        print(f"  → Not a simple integer")
        print(f"  → Repr: {repr(data_result)}")
        
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()

# Test bridge extraction
print("\n[4] Testing bridge extraction...")
try:
    tensor_data = ftb.TensorNetworkHelper.extract_tensor_data(state, 0)
    print(f"✓ Extraction successful!")
    print(f"  Shape: {tensor_data.shape}")
    print(f"  Dtype: {tensor_data.dtype}")
    print(f"  First element: {tensor_data.flat[0]}")
    
    # Verify it's a Hadamard gate
    expected_h = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    if tensor_data.shape == (2, 2):
        matches = np.allclose(tensor_data, expected_h, rtol=1e-5)
        print(f"  Matches H gate: {matches}")
        if matches:
            print("  ✓ Data extraction is CORRECT!")
        else:
            print(f"  ✗ Data mismatch!")
            print(f"    Expected:\n{expected_h}")
            print(f"    Got:\n{tensor_data}")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)


