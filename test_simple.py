#!/home/u4876763/miniforge3/envs/cudaq-test/bin/python3
"""
Simple FormoTensor Backend Test
Tests two types of kernels with FormoTensor backends
"""

import cudaq
import numpy as np

def test_backend(backend_name):
    """Test a specific backend with two simple kernels"""
    print(f"\n--- Testing {backend_name} ---")
    
    try:
        # Set the target backend
        cudaq.set_target(backend_name)
        print(f"✓ Successfully set target to {backend_name}")
    except Exception as e:
        print(f"❌ Failed to set target {backend_name}: {e}")
        return False
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Simple Bell state circuit
    try:
        @cudaq.kernel
        def bell_circuit():
            qubits = cudaq.qvector(2)
            h(qubits[0])
            cx(qubits[0], qubits[1])
            mz(qubits)
        
        result = cudaq.sample(bell_circuit)
        print(f"✓ Bell circuit: {len(result)} samples")
        success_count += 1
    except Exception as e:
        print(f"❌ Bell circuit failed: {e}")
    
    # Test 2: Parameterized circuit
    try:
        @cudaq.kernel
        def parameterized_circuit(theta: float):
            qubit = cudaq.qubit()
            ry(theta, qubit)
            mz(qubit)
        
        result = cudaq.sample(parameterized_circuit, np.pi/4)
        print(f"✓ Parameterized circuit: {len(result)} samples") 
        success_count += 1
    except Exception as e:
        print(f"❌ Parameterized circuit failed: {e}")
    
    print(f"Backend {backend_name}: {success_count}/{total_tests} tests passed")
    return success_count == total_tests

def main():
    print("="*60)
    print("  FormoTensor Simple Backend Test")
    print("="*60)
    print(f"CUDA-Q version: {cudaq.__version__}")
    
    # Test the four FormoTensor backends directly
    backends_to_test = ['formotensor', 'formotensor-mps', 'formotensor-fp32', 'formotensor-mps-fp32']
    
    print(f"\nTesting {len(backends_to_test)} FormoTensor backends:")
    for backend in backends_to_test:
        print(f"  - {backend}")
    
    # Test each backend
    working_backends = 0
    for backend in backends_to_test:
        if test_backend(backend):
            working_backends += 1
    
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)
    print(f"Backends tested: {len(backends_to_test)}")
    print(f"Working backends: {working_backends}")
    print(f"Success rate: {working_backends/len(backends_to_test)*100:.1f}%")
    
    return working_backends > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
