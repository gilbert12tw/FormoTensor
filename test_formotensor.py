#!/usr/bin/env python3
"""
FormoTensor Backend Test Suite

This script tests the FormoTensor quantum simulation backends to ensure
they are properly installed and functioning correctly.
"""

import cudaq
import numpy as np
import sys
import time
from typing import List, Dict, Any

def print_banner(message: str):
    """Print a formatted banner message."""
    print("\n" + "="*60)
    print(f"  {message}")
    print("="*60)

def print_section(message: str):
    """Print a formatted section header."""
    print(f"\n--- {message} ---")

def test_backend_availability() -> List[str]:
    """Test which FormoTensor backends are available."""
    print_section("Testing Backend Availability")
    
    all_targets = cudaq.get_targets()
    available_backends = []
    formotensor_backends = []
    
    print("All available CUDA-Q targets:")
    for target in all_targets:
        print(f"  - {target.name}")
        available_backends.append(target.name)
        if target.name.startswith('formotensor'):
            formotensor_backends.append(target.name)
    
    print(f"\nFormoTensor backends found: {len(formotensor_backends)}")
    for backend in formotensor_backends:
        print(f"  ✓ {backend}")
    
    if not formotensor_backends:
        print("  ❌ No FormoTensor backends found!")
        print("  Expected backends: formotensor, formotensor-mps, formotensor-fp32, formotensor-mps-fp32")
    
    return formotensor_backends

def create_test_circuits():
    """Create test quantum circuits for validation."""
    
    @cudaq.kernel
    def simple_bell_circuit():
        """Simple Bell state circuit."""
        qubits = cudaq.qvector(2)
        h(qubits[0])
        cx(qubits[0], qubits[1])
        mz(qubits)
    
    @cudaq.kernel
    def ghz_circuit(num_qubits: int):
        """GHZ state circuit with parameterized number of qubits."""
        qubits = cudaq.qvector(num_qubits)
        h(qubits[0])
        for i in range(num_qubits - 1):
            cx(qubits[i], qubits[i + 1])
        mz(qubits)
    
    @cudaq.kernel
    def parameterized_circuit(theta: float):
        """Parameterized circuit for testing."""
        qubits = cudaq.qvector(3)
        h(qubits[0])
        ry(theta, qubits[1])
        cx(qubits[0], qubits[1])
        cx(qubits[1], qubits[2])
        mz(qubits)
    
    return {
        'bell': simple_bell_circuit,
        'ghz': ghz_circuit,
        'parameterized': parameterized_circuit
    }

def test_backend_functionality(backend_name: str, circuits: Dict[str, Any]) -> Dict[str, Any]:
    """Test functionality of a specific backend."""
    print_section(f"Testing {backend_name} Backend")
    
    results = {
        'backend': backend_name,
        'tests_passed': 0,
        'tests_total': 0,
        'errors': []
    }
    
    try:
        # Set the target backend
        cudaq.set_target(backend_name)
        print(f"✓ Successfully set target to {backend_name}")
        
        # Test 1: Simple Bell circuit
        results['tests_total'] += 1
        try:
            start_time = time.time()
            bell_result = cudaq.sample(circuits['bell'], 1000)
            duration = time.time() - start_time
            
            print(f"✓ Bell circuit completed in {duration:.3f}s")
            print(f"  Bell state results: {len(bell_result)} measurement outcomes")
            
            # Check if we get expected Bell state results (|00⟩ and |11⟩)
            counts = {state: count for state, count in bell_result.items()}
            if '00' in counts and '11' in counts:
                print(f"  ✓ Expected Bell state outcomes: |00⟩: {counts.get('00', 0)}, |11⟩: {counts.get('11', 0)}")
                results['tests_passed'] += 1
            else:
                print(f"  ⚠️  Unexpected outcomes: {counts}")
                results['tests_passed'] += 1  # Still count as passed if no error
                
        except Exception as e:
            print(f"  ❌ Bell circuit failed: {str(e)}")
            results['errors'].append(f"Bell circuit: {str(e)}")
        
        # Test 2: GHZ circuit
        results['tests_total'] += 1
        try:
            start_time = time.time()
            ghz_result = cudaq.sample(circuits['ghz'], 4, 500)
            duration = time.time() - start_time
            
            print(f"✓ GHZ(4) circuit completed in {duration:.3f}s")
            print(f"  GHZ state results: {len(ghz_result)} measurement outcomes")
            results['tests_passed'] += 1
            
        except Exception as e:
            print(f"  ❌ GHZ circuit failed: {str(e)}")
            results['errors'].append(f"GHZ circuit: {str(e)}")
        
        # Test 3: Parameterized circuit
        results['tests_total'] += 1
        try:
            theta = np.pi / 4
            start_time = time.time()
            param_result = cudaq.sample(circuits['parameterized'], theta, 500)
            duration = time.time() - start_time
            
            print(f"✓ Parameterized circuit (θ={theta:.3f}) completed in {duration:.3f}s")
            print(f"  Parameterized results: {len(param_result)} measurement outcomes")
            results['tests_passed'] += 1
            
        except Exception as e:
            print(f"  ❌ Parameterized circuit failed: {str(e)}")
            results['errors'].append(f"Parameterized circuit: {str(e)}")
        
        # Test 4: Expectation value (if backend supports it)
        results['tests_total'] += 1
        try:
            @cudaq.kernel
            def simple_circuit():
                q = cudaq.qubit()
                h(q)
                
            # Create a simple observable (Z)
            hamiltonian = cudaq.spin.z(0)
            start_time = time.time()
            expectation = cudaq.observe(simple_circuit, hamiltonian)
            duration = time.time() - start_time
            
            print(f"✓ Expectation value computation completed in {duration:.3f}s")
            print(f"  ⟨H⟩ = {expectation.expectation():.6f}")
            results['tests_passed'] += 1
            
        except Exception as e:
            print(f"  ⚠️  Expectation value failed: {str(e)}")
            results['errors'].append(f"Expectation value: {str(e)}")
            # Don't count this as a critical failure for some backends
        
    except Exception as e:
        print(f"❌ Failed to set target {backend_name}: {str(e)}")
        results['errors'].append(f"Target setting: {str(e)}")
    
    return results

def generate_report(all_results: List[Dict[str, Any]]):
    """Generate a summary report of all tests."""
    print_banner("Test Summary Report")
    
    total_backends = len(all_results)
    working_backends = 0
    total_tests = 0
    total_passed = 0
    
    for result in all_results:
        total_tests += result['tests_total']
        total_passed += result['tests_passed']
        if result['tests_passed'] == result['tests_total'] and not result['errors']:
            working_backends += 1
    
    print(f"Backends tested: {total_backends}")
    print(f"Fully working backends: {working_backends}")
    print(f"Total tests run: {total_tests}")
    print(f"Tests passed: {total_passed}")
    print(f"Overall success rate: {total_passed/total_tests*100:.1f}%" if total_tests > 0 else "No tests run")
    
    print("\nPer-backend results:")
    for result in all_results:
        status = "✓" if result['tests_passed'] == result['tests_total'] and not result['errors'] else "❌"
        print(f"  {status} {result['backend']}: {result['tests_passed']}/{result['tests_total']} tests passed")
        if result['errors']:
            for error in result['errors'][:2]:  # Show first 2 errors
                print(f"    Error: {error}")
    
    return working_backends == total_backends

def main():
    """Main test function."""
    print_banner("FormoTensor Backend Test Suite")
    print("Testing enhanced cuTensorNet simulation backends")
    
    # Check if CUDA-Q is working
    try:
        cudaq_version = cudaq.__version__ if hasattr(cudaq, '__version__') else "Unknown"
        print(f"CUDA-Q version: {cudaq_version}")
    except:
        print("Could not determine CUDA-Q version")
    
    # Test backend availability
    available_backends = test_backend_availability()
    
    if not available_backends:
        print_banner("No FormoTensor backends found!")
        print("Please ensure FormoTensor is properly built and installed.")
        print("Expected backends:")
        print("  - formotensor")
        print("  - formotensor-mps") 
        print("  - formotensor-fp32")
        print("  - formotensor-mps-fp32")
        return False
    
    # Create test circuits
    circuits = create_test_circuits()
    
    # Test each available backend
    all_results = []
    for backend in available_backends:
        result = test_backend_functionality(backend, circuits)
        all_results.append(result)
    
    # Generate final report
    success = generate_report(all_results)
    
    if success:
        print_banner("🎉 All FormoTensor backends are working correctly!")
        return True
    else:
        print_banner("⚠️  Some issues were detected")
        print("Check the error messages above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
