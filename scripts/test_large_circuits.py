#!/usr/bin/env python3
"""
Test TensorNet extraction with larger quantum circuits

This script tests the extraction of tensor networks from various
quantum circuits of increasing complexity.
"""

import cudaq
import formotensor_bridge as ftb
import numpy as np
import time
from typing import Dict, List, Tuple

print("=" * 80)
print("Large Circuit TensorNet Extraction Test")
print("=" * 80)

cudaq.set_target("tensornet")

# ============================================================================
# Test Circuits
# ============================================================================

@cudaq.kernel
def small_circuit():
    """2-qubit Bell state"""
    q = cudaq.qvector(2)
    h(q[0])
    cx(q[0], q[1])

@cudaq.kernel
def medium_circuit():
    """5-qubit GHZ state"""
    q = cudaq.qvector(5)
    h(q[0])
    for i in range(4):
        cx(q[i], q[i+1])

@cudaq.kernel
def large_circuit():
    """10-qubit entangled state with multiple layers"""
    q = cudaq.qvector(10)
    
    # Layer 1: Hadamard on all qubits
    for i in range(10):
        h(q[i])
    
    # Layer 2: Entanglement
    for i in range(9):
        cx(q[i], q[i+1])
    
    # Layer 3: Rotation gates
    for i in range(10):
        rz(0.5, q[i])

@cudaq.kernel
def very_large_circuit():
    """15-qubit circuit with complex structure"""
    q = cudaq.qvector(15)
    
    # Layer 1: Initialize with Hadamard
    for i in range(15):
        h(q[i])
    
    # Layer 2: Nearest-neighbor entanglement
    for i in range(14):
        cx(q[i], q[i+1])
    
    # Layer 3: Rotation layer
    for i in range(15):
        rx(0.3, q[i])
        ry(0.4, q[i])
    
    # Layer 4: Additional entanglement
    for i in range(0, 14, 2):
        cx(q[i], q[i+1])

@cudaq.kernel
def qaoa_like_circuit():
    """8-qubit QAOA-like circuit"""
    q = cudaq.qvector(8)
    
    # Initialize in superposition
    for i in range(8):
        h(q[i])
    
    # Problem Hamiltonian layer
    for i in range(7):
        cx(q[i], q[i+1])
        rz(0.5, q[i+1])
        cx(q[i], q[i+1])
    
    # Mixer Hamiltonian layer
    for i in range(8):
        rx(0.3, q[i])

# ============================================================================
# Test Functions
# ============================================================================

def analyze_circuit(name: str, circuit) -> Dict:
    """Analyze a circuit and extract its tensor network"""
    print(f"\n{'='*80}")
    print(f"Circuit: {name}")
    print('='*80)
    
    results = {
        'name': name,
        'success': False,
        'num_qubits': 0,
        'num_tensors': 0,
        'total_elements': 0,
        'total_memory_kb': 0,
        'extraction_time_ms': 0,
        'tensors': []
    }
    
    try:
        # Get state
        start_time = time.time()
        state = cudaq.get_state(circuit)
        state_time = time.time() - start_time
        
        # Check tensor network support
        if not ftb.TensorNetworkHelper.has_tensors(state):
            print("✗ No tensor network support")
            return results
        
        # Get basic info
        num_qubits = ftb.TensorNetworkHelper.get_num_qubits(state)
        all_info = ftb.TensorNetworkHelper.get_all_tensors_info(state)
        
        print(f"\n📊 Circuit Statistics:")
        print(f"  Qubits: {num_qubits}")
        print(f"  Tensors in network: {len(all_info)}")
        print(f"  State creation time: {state_time*1000:.2f} ms")
        
        # Analyze tensor structure
        print(f"\n🔍 Tensor Network Structure:")
        print("-" * 80)
        
        total_elements = 0
        total_memory = 0
        tensor_details = []
        
        for i, info in enumerate(all_info):
            tensor_detail = {
                'index': i,
                'shape': info.shape,
                'dimensions': len(info.shape),
                'elements': info.total_elements,
                'size_kb': info.size_bytes / 1024
            }
            tensor_details.append(tensor_detail)
            
            total_elements += info.total_elements
            total_memory += info.size_bytes
            
            # Print tensor info
            print(f"\nTensor {i}:")
            print(f"  Shape: {info.shape}")
            print(f"  Dimensions: {len(info.shape)}D")
            print(f"  Elements: {info.total_elements:,}")
            print(f"  Size: {info.size_bytes / 1024:.2f} KB")
            
            # Classify tensor type
            if len(info.shape) == 2 and info.shape[0] == 2:
                print(f"  Type: Single-qubit gate")
            elif len(info.shape) == 4:
                print(f"  Type: Two-qubit gate")
            else:
                print(f"  Type: {len(info.shape)}-dimensional tensor")
        
        print(f"\n{'='*80}")
        print(f"Network Summary:")
        print(f"  Total tensors: {len(all_info)}")
        print(f"  Total elements: {total_elements:,}")
        print(f"  Total memory: {total_memory / 1024:.2f} KB")
        print(f"  Average tensor size: {total_memory / len(all_info) / 1024:.2f} KB")
        
        # Test data extraction
        print(f"\n🔬 Testing Data Extraction:")
        print("-" * 80)
        
        extraction_times = []
        num_samples = min(3, len(all_info))  # Extract first 3 tensors
        
        for i in range(num_samples):
            try:
                start_time = time.time()
                data = ftb.TensorNetworkHelper.extract_tensor_data(state, i)
                extract_time = (time.time() - start_time) * 1000
                extraction_times.append(extract_time)
                
                print(f"\nTensor {i}:")
                print(f"  ✓ Extraction successful")
                print(f"  Time: {extract_time:.3f} ms")
                print(f"  Shape: {data.shape}")
                print(f"  Dtype: {data.dtype}")
                print(f"  Norm: {np.linalg.norm(data):.6f}")
                print(f"  Max |element|: {np.max(np.abs(data)):.6f}")
                
                # Verify data integrity
                if np.any(np.isnan(data)):
                    print(f"  ⚠️  Contains NaN values!")
                if np.any(np.isinf(data)):
                    print(f"  ⚠️  Contains Inf values!")
                
            except Exception as e:
                print(f"\nTensor {i}:")
                print(f"  ✗ Extraction failed: {e}")
        
        if extraction_times:
            avg_extraction_time = np.mean(extraction_times)
            print(f"\n{'='*80}")
            print(f"Extraction Performance:")
            print(f"  Average time: {avg_extraction_time:.3f} ms")
            print(f"  Min time: {min(extraction_times):.3f} ms")
            print(f"  Max time: {max(extraction_times):.3f} ms")
        else:
            avg_extraction_time = 0
        
        # Update results
        results.update({
            'success': True,
            'num_qubits': num_qubits,
            'num_tensors': len(all_info),
            'total_elements': total_elements,
            'total_memory_kb': total_memory / 1024,
            'extraction_time_ms': avg_extraction_time,
            'tensors': tensor_details
        })
        
        print(f"\n✓ Analysis complete")
        
    except Exception as e:
        print(f"\n✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    return results

# ============================================================================
# Main Test Suite
# ============================================================================

def main():
    """Run all circuit tests"""
    
    circuits = [
        ("Small (2-qubit Bell)", small_circuit),
        ("Medium (5-qubit GHZ)", medium_circuit),
        ("Large (10-qubit Multi-layer)", large_circuit),
        ("Very Large (15-qubit)", very_large_circuit),
        ("QAOA-like (8-qubit)", qaoa_like_circuit),
    ]
    
    all_results = []
    
    for name, circuit in circuits:
        result = analyze_circuit(name, circuit)
        all_results.append(result)
        time.sleep(0.5)  # Brief pause between tests
    
    # ========================================================================
    # Summary Report
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    
    print(f"\n{'Circuit':<30} {'Qubits':<8} {'Tensors':<10} {'Elements':<12} {'Memory (KB)':<12} {'Extract (ms)':<12}")
    print("-" * 80)
    
    for result in all_results:
        if result['success']:
            print(f"{result['name']:<30} "
                  f"{result['num_qubits']:<8} "
                  f"{result['num_tensors']:<10} "
                  f"{result['total_elements']:<12,} "
                  f"{result['total_memory_kb']:<12.2f} "
                  f"{result['extraction_time_ms']:<12.3f}")
        else:
            print(f"{result['name']:<30} {'FAILED':<8}")
    
    # Statistics
    successful = [r for r in all_results if r['success']]
    if successful:
        print(f"\n{'='*80}")
        print("Statistics:")
        print(f"  Successful tests: {len(successful)}/{len(all_results)}")
        print(f"  Total qubits tested: {sum(r['num_qubits'] for r in successful)}")
        print(f"  Total tensors extracted: {sum(r['num_tensors'] for r in successful)}")
        print(f"  Total elements: {sum(r['total_elements'] for r in successful):,}")
        print(f"  Total memory: {sum(r['total_memory_kb'] for r in successful):.2f} KB")
        print(f"  Average extraction time: {np.mean([r['extraction_time_ms'] for r in successful]):.3f} ms")
    
    # ========================================================================
    # Scaling Analysis
    # ========================================================================
    
    print(f"\n{'='*80}")
    print("Scaling Analysis:")
    print('='*80)
    
    if len(successful) >= 2:
        qubits = [r['num_qubits'] for r in successful]
        tensors = [r['num_tensors'] for r in successful]
        elements = [r['total_elements'] for r in successful]
        
        print(f"\nTensor count vs Qubits:")
        for i, r in enumerate(successful):
            ratio = r['num_tensors'] / r['num_qubits'] if r['num_qubits'] > 0 else 0
            print(f"  {r['num_qubits']} qubits → {r['num_tensors']} tensors (ratio: {ratio:.2f})")
        
        print(f"\nMemory scaling:")
        for i, r in enumerate(successful):
            mem_per_qubit = r['total_memory_kb'] / r['num_qubits'] if r['num_qubits'] > 0 else 0
            print(f"  {r['num_qubits']} qubits → {r['total_memory_kb']:.2f} KB ({mem_per_qubit:.2f} KB/qubit)")
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)
    
    # Return results for further analysis
    return all_results

if __name__ == "__main__":
    results = main()



