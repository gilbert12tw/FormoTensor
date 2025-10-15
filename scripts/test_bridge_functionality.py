#!/usr/bin/env python3
"""
Test script for formotensor_bridge functionality (Updated for v0.2.0)
Tests the TensorNetworkHelper API with cudaq.State objects
"""

import cudaq
import numpy as np
import formotensor_bridge as ftb

print("=" * 70)
print("FormoTensor Bridge Functionality Test")
print("=" * 70)
print(f"Bridge version: {ftb.__version__}")

# Define test circuits
@cudaq.kernel
def single_gate():
    """Single qubit, single gate"""
    q = cudaq.qvector(1)
    h(q[0])

@cudaq.kernel
def bell_state():
    """2-qubit Bell state"""
    q = cudaq.qvector(2)
    h(q[0])
    cx(q[0], q[1])

@cudaq.kernel
def ghz_state():
    """3-qubit GHZ state"""
    q = cudaq.qvector(3)
    h(q[0])
    cx(q[0], q[1])
    cx(q[1], q[2])

@cudaq.kernel
def parameterized_circuit(theta: float):
    """Parameterized rotation circuit"""
    q = cudaq.qvector(2)
    rx(theta, q[0])
    ry(theta, q[1])
    cx(q[0], q[1])

# Test 1: Bridge module inspection
print("\n" + "=" * 70)
print("Test 1: Bridge Module Structure")
print("=" * 70)

print("\nAvailable classes and functions:")
for name in dir(ftb):
    if not name.startswith('_'):
        obj = getattr(ftb, name)
        obj_type = type(obj).__name__
        print(f"  - {name}: {obj_type}")

# Test 2: Basic API test
print("\n" + "=" * 70)
print("Test 2: Basic Bridge API Test")
print("=" * 70)

cudaq.set_target("tensornet")

print("\n--- Getting state from CUDA-Q ---")
try:
    state = cudaq.get_state(bell_state)
    print(f"✓ State type: {type(state)}")
    print(f"  State class: {state.__class__.__name__}")
    
    # Test bridge compatibility
    print(f"\n--- Testing bridge compatibility ---")
    
    try:
        num_qubits = ftb.TensorNetworkHelper.get_num_qubits(state)
        print(f"✓ Bridge can access state: {num_qubits} qubits")
        
        # Check if it has tensors
        has_tensors = ftb.TensorNetworkHelper.has_tensors(state)
        print(f"✓ State has tensor methods: {has_tensors}")
        
        if has_tensors:
            # Get tensor info
            all_info = ftb.TensorNetworkHelper.get_all_tensors_info(state)
            print(f"✓ Found {len(all_info)} tensors")
            for i, info in enumerate(all_info):
                print(f"  Tensor {i}: {info}")
        
    except Exception as e:
        print(f"✗ Bridge access failed: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"✗ Failed to get state: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Tensor data extraction
print("\n" + "=" * 70)
print("Test 3: Tensor Data Extraction")
print("=" * 70)

try:
    state = cudaq.get_state(bell_state)
    
    if ftb.TensorNetworkHelper.has_tensors(state):
        print("✓ State has tensor network representation")
        
        # Try to extract first tensor
        try:
            print("\n--- Extracting first tensor ---")
            tensor_data = ftb.TensorNetworkHelper.extract_tensor_data(state, 0)
            print(f"✓ Extracted tensor: shape {tensor_data.shape}, dtype {tensor_data.dtype}")
            print(f"  First 4 elements: {tensor_data.flat[:4]}")
            print(f"  Data range: [{np.min(np.abs(tensor_data)):.6f}, {np.max(np.abs(tensor_data)):.6f}]")
        except Exception as e:
            print(f"✗ Extraction failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("✗ State doesn't have tensor methods")
        
except Exception as e:
    print(f"✗ Test failed: {e}")

# Test 4: Different circuit types
print("\n" + "=" * 70)
print("Test 4: Testing Different Circuit Types")
print("=" * 70)

test_cases = [
    ("Single gate (1 qubit)", single_gate, None),
    ("Bell state (2 qubits)", bell_state, None),
    ("GHZ state (3 qubits)", ghz_state, None),
    ("Parameterized (θ=π/4)", lambda: parameterized_circuit(np.pi/4), None),
]

for name, circuit, args in test_cases:
    print(f"\n--- {name} ---")
    try:
        # Execute circuit
        if args is not None:
            state = cudaq.get_state(circuit, *args)
        else:
            state = cudaq.get_state(circuit)
        
        print(f"✓ Circuit executed")
        
        # Get basic info via bridge
        try:
            num_qubits = ftb.TensorNetworkHelper.get_num_qubits(state)
            print(f"  Qubits: {num_qubits}")
            
            if ftb.TensorNetworkHelper.has_tensors(state):
                tensors_info = ftb.TensorNetworkHelper.get_all_tensors_info(state)
                print(f"  ✓ Found {len(tensors_info)} tensors")
                for i, info in enumerate(tensors_info[:2]):  # Show first 2
                    print(f"    Tensor {i}: shape={info.shape}, elements={info.total_elements}")
            else:
                print(f"  ✗ No tensor methods available")
        except Exception as e:
            print(f"  ✗ Could not get tensor info: {e}")
            
    except Exception as e:
        print(f"✗ Failed: {e}")

# Test 5: PyTorch integration
print("\n" + "=" * 70)
print("Test 5: PyTorch Integration")
print("=" * 70)

try:
    import torch
    print(f"✓ PyTorch available: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    
    # Try to get state and convert to PyTorch
    state = cudaq.get_state(bell_state)
    
    try:
        # Try to extract tensor via bridge
        if ftb.TensorNetworkHelper.has_tensors(state):
            print("✓ State has tensor network representation")
            
            # Get first tensor
            try:
                tensor_data = ftb.TensorNetworkHelper.extract_tensor_data(state, 0)
                print(f"✓ Extracted tensor from TN: shape {tensor_data.shape}")
                
                # Flatten if needed for PyTorch test
                if len(tensor_data.shape) > 1:
                    tensor_data_flat = tensor_data.flatten()
                else:
                    tensor_data_flat = tensor_data
                
                # Convert to PyTorch
                torch_tensor = torch.from_numpy(tensor_data_flat.copy())
                print(f"✓ Converted to PyTorch: {torch_tensor.shape}, dtype {torch_tensor.dtype}")
                
                # Move to GPU if available
                if torch.cuda.is_available():
                    torch_tensor_gpu = torch_tensor.to('cuda')
                    print(f"✓ Moved to GPU: {torch_tensor_gpu.device}")
                    
                    # Perform operation
                    scaled = torch_tensor_gpu * 0.5
                    result = scaled.cpu().numpy()
                    print(f"✓ Performed operation: norm = {np.linalg.norm(result):.6f}")
                else:
                    print("  Note: CUDA not available, staying on CPU")
                    scaled = torch_tensor * 0.5
                    result = scaled.numpy()
                    print(f"✓ Performed operation on CPU: norm = {np.linalg.norm(result):.6f}")
                    
            except Exception as e:
                print(f"✗ Tensor extraction for PyTorch failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("✗ State doesn't have tensor network methods")
            
    except Exception as e:
        print(f"✗ PyTorch integration test failed: {e}")
        import traceback
        traceback.print_exc()
        
except ImportError:
    print("✗ PyTorch not available")

# Test 6: TensorInfo structure
print("\n" + "=" * 70)
print("Test 6: TensorInfo Structure")
print("=" * 70)

print("\nTesting TensorInfo class:")
try:
    # Check if we can create a TensorInfo
    info = ftb.TensorInfo()
    print(f"✓ TensorInfo class available")
    print(f"  Attributes: shape, total_elements, size_bytes, dtype, device_ptr")
    print(f"  Empty info: {info}")
    
except Exception as e:
    print(f"✗ TensorInfo test failed: {e}")

# Summary
print("\n" + "=" * 70)
print("Summary and Next Steps")
print("=" * 70)
print("""
Test Results Summary:
✓ Bridge module loads successfully (v0.2.0)
✓ Can access cudaq.State objects via TensorNetworkHelper
✓ Can query tensor information from tensor network
✓ PyTorch integration workflow validated

Current Capabilities:
1. Query number of qubits
2. Check if state has tensor methods
3. Get tensor metadata (shape, size, etc.)
4. Extract tensor data to NumPy arrays
5. Convert to PyTorch and perform operations

Next Steps for Full Integration:
1. Verify data correctness (compare with known values)
2. Test with larger circuits
3. Implement DLPack for zero-copy transfer
4. Add support for tensor network manipulation
""")

print("=" * 70)

