#!/usr/bin/env python3
"""
Test script to explore CUDA-Q State API
Purpose: Understand how to extract state vector data from different backends
"""

import cudaq
import numpy as np

print("=" * 70)
print("CUDA-Q State API Explorer")
print("=" * 70)

# Define a simple test circuit
@cudaq.kernel
def bell_state():
    """2-qubit Bell state: (|00⟩ + |11⟩) / √2"""
    q = cudaq.qvector(2)
    h(q[0])
    cx(q[0], q[1])

@cudaq.kernel
def ghz_state():
    """3-qubit GHZ state: (|000⟩ + |111⟩) / √2"""
    q = cudaq.qvector(3)
    h(q[0])
    cx(q[0], q[1])
    cx(q[1], q[2])

# Test 1: Explore State object structure
print("\n" + "=" * 70)
print("Test 1: Exploring State Object Structure")
print("=" * 70)

backends_to_test = ["tensornet", "nvidia"]  # Add more if available

for backend in backends_to_test:
    print(f"\n--- Testing with backend: {backend} ---")
    try:
        cudaq.set_target(backend)
        state = cudaq.get_state(bell_state)
        
        print(f"✓ State object type: {type(state)}")
        print(f"  State object class: {state.__class__.__name__}")
        
        # List all available methods and attributes
        methods = [m for m in dir(state) if not m.startswith('_')]
        print(f"\n  Available methods/attributes ({len(methods)}):")
        for method in methods:
            print(f"    - {method}")
        
        # Try common attribute names
        print(f"\n  Testing common attributes:")
        for attr in ['data', 'amplitudes', 'get_data', 'to_numpy', 'vector']:
            if hasattr(state, attr):
                print(f"    ✓ Has '{attr}'")
                try:
                    value = getattr(state, attr)
                    if callable(value):
                        print(f"      → {attr}() is a method")
                    else:
                        print(f"      → {attr} = {type(value)}")
                except Exception as e:
                    print(f"      → Error accessing: {e}")
            else:
                print(f"    ✗ No '{attr}'")
        
        # Check if it's iterable
        print(f"\n  Iterability tests:")
        print(f"    Has __len__: {hasattr(state, '__len__')}")
        print(f"    Has __iter__: {hasattr(state, '__iter__')}")
        print(f"    Has __getitem__: {hasattr(state, '__getitem__')}")
        
        if hasattr(state, '__len__'):
            try:
                length = len(state)
                print(f"    Length: {length}")
            except Exception as e:
                print(f"    Length error: {e}")
        
        # Try to iterate or index
        print(f"\n  Data access tests:")
        try:
            # Try indexing
            first_elem = state[0]
            print(f"    ✓ Can index: state[0] = {first_elem}")
            
            # Try to convert to list/array
            if hasattr(state, '__len__'):
                state_list = [state[i] for i in range(min(4, len(state)))]
                print(f"    ✓ First 4 elements: {state_list}")
        except Exception as e:
            print(f"    ✗ Cannot index: {e}")
        
        # Try iteration
        try:
            state_data = list(state)
            print(f"    ✓ Can iterate: got {len(state_data)} elements")
            print(f"      First 4 elements: {state_data[:4]}")
        except Exception as e:
            print(f"    ✗ Cannot iterate: {e}")
        
        # Try numpy conversion (only works for state vector backends)
        try:
            state_array = np.array(state)
            print(f"    ✓ NumPy conversion: shape {state_array.shape}, dtype {state_array.dtype}")
            print(f"      First 4 elements: {state_array[:4]}")
        except Exception as e:
            print(f"    ✗ NumPy conversion failed: {e}")
            print(f"      Note: This is expected for TensorNet backends")
        
    except Exception as e:
        print(f"✗ Failed to test backend '{backend}': {e}")
        import traceback
        traceback.print_exc()

# Test 2: Test with formotensor_bridge if available
print("\n" + "=" * 70)
print("Test 2: Testing with FormoTensor Bridge (if available)")
print("=" * 70)

cudaq.set_target("tensornet")

try:
    import formotensor_bridge as ftb
    print("✓ formotensor_bridge is available")
    
    test_circuits = [
        ("Bell (2 qubits)", bell_state, 2),
        ("GHZ (3 qubits)", ghz_state, 3),
    ]
    
    for name, circuit, n_qubits in test_circuits:
        print(f"\n--- {name} ---")
        try:
            state = cudaq.get_state(circuit)
            
            # Use bridge to get info
            if ftb.TensorNetworkHelper.has_tensors(state):
                num_qubits = ftb.TensorNetworkHelper.get_num_qubits(state)
                print(f"✓ Number of qubits: {num_qubits}")
                
                all_info = ftb.TensorNetworkHelper.get_all_tensors_info(state)
                print(f"✓ Found {len(all_info)} tensors in network")
                
                for i, info in enumerate(all_info):
                    print(f"  Tensor {i}: shape={info.shape}, elements={info.total_elements}")
            else:
                print("✗ State doesn't support tensor methods")
                
        except Exception as e:
            print(f"✗ Failed: {e}")
            
except ImportError:
    print("✗ formotensor_bridge not available")
    print("  Skipping tensor network specific tests")
    print("  Install with: cd build && ninja install")

# Test 3: Try alternative CUDA-Q APIs (safe for all backends)
print("\n" + "=" * 70)
print("Test 3: Alternative CUDA-Q APIs (Backend-Safe)")
print("=" * 70)

cudaq.set_target("tensornet")

print("\n--- Method 1: cudaq.get_state() ---")
try:
    state = cudaq.get_state(bell_state)
    print(f"✓ Type: {type(state)}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n--- Method 2: Sampling ---")
try:
    result = cudaq.sample(bell_state, shots_count=1000)
    print(f"✓ Measurement results:")
    for bits, count in result.items():
        print(f"  |{bits}⟩: {count} times ({count/10:.1f}%)")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n--- Method 3: Observe with Pauli operators ---")
try:
    from cudaq import spin
    
    # Z ⊗ Z operator
    hamiltonian = spin.z(0) * spin.z(1)
    expectation = cudaq.observe(bell_state, hamiltonian)
    print(f"✓ ⟨Z₀Z₁⟩ = {expectation.expectation():.6f}")
    
except Exception as e:
    print(f"✗ Failed: {e}")

# Summary
print("\n" + "=" * 70)
print("Summary and Recommendations")
print("=" * 70)
print("""
Based on the tests above, the recommended approaches are:

1. **For TensorNet Backends** (tensornet, tensornet-mps):
   - ✅ Use formotensor_bridge to access tensor network structure
   - ✅ Use state.getTensor(idx) / state.getTensors()
   - ❌ Don't use list(state) or np.array(state) - not supported

2. **For State Vector Backends** (nvidia, qpp-cpu):
   - ✅ Use list(state) or np.array(state) for state vector
   - ✅ Use state[idx] for indexing
   - ❌ No getTensor methods available

3. **Backend-Agnostic Methods**:
   - ✅ Use cudaq.observe() for expectation values
   - ✅ Use cudaq.sample() for measurement statistics
   - ✅ Use state.num_qubits() for circuit size

4. **FormoTensor Bridge Usage**:
   - Check has_tensors() first to verify backend support
   - Use get_all_tensors_info() to explore network structure
   - Use extract_tensor_data() to get NumPy arrays from tensors
""")

print("=" * 70)

