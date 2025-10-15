# FormoTensor Python Bridge

A simple pybind11 interface for extracting Tensor Networks from CUDA-Q circuits.

## Features

1. **Extract Tensor Network Information**: Get tensor metadata from CUDA-Q circuits
2. **Extract Tensor Data**: Copy tensor data from GPU to NumPy arrays (using NumPy copy method)
3. **PyTorch Integration**: Easy conversion to PyTorch tensors for further operations
4. **DLPack Optimization (Planned)**: Future zero-copy transfer support

## Build and Installation

```bash
# From FormoTensor root directory
./REBUILD.sh
```

This will build and install the `formotensor_bridge` module to your Python environment.

## Usage Example

```python
import cudaq
import formotensor_bridge as ftb
import numpy as np
import torch

# 1. Set tensornet backend
cudaq.set_target("tensornet")

# 2. Define quantum circuit
@cudaq.kernel
def bell_circuit():
    q = cudaq.qvector(2)
    h(q[0])
    cx(q[0], q[1])

# 3. Get quantum state
state = cudaq.get_state(bell_circuit)

# 4. Check if state supports tensor network
if ftb.TensorNetworkHelper.has_tensors(state):
    # 5. Get number of qubits
    num_qubits = ftb.TensorNetworkHelper.get_num_qubits(state)
    print(f"Qubits: {num_qubits}")
    
    # 6. Get all tensor information
    all_info = ftb.TensorNetworkHelper.get_all_tensors_info(state)
    print(f"Tensors: {len(all_info)}")
    
    # 7. Extract tensor data (NumPy copy from GPU to CPU)
    tensor_data = ftb.TensorNetworkHelper.extract_tensor_data(state, 0)
    print(f"Tensor shape: {tensor_data.shape}")
    
    # 8. Convert to PyTorch
    torch_tensor = torch.from_numpy(tensor_data)
    
    # 9. Move to GPU (if available)
    if torch.cuda.is_available():
        torch_tensor = torch_tensor.to('cuda')
    
    # 10. Perform operations in PyTorch
    modified_tensor = torch_tensor * 0.5
    
    # 11. Convert back to NumPy (if needed)
    result_numpy = modified_tensor.cpu().numpy()
```

## API Reference

### `TensorNetworkHelper`

Static helper class for tensor network operations.

#### Methods

- `get_num_qubits(state) -> int`
  - Get the number of qubits in the quantum state

- `has_tensors(state) -> bool`
  - Check if the state supports tensor network extraction

- `get_tensor_info(state, idx) -> TensorInfo`
  - Get metadata for a specific tensor (without extracting data)

- `extract_tensor_data(state, idx) -> np.ndarray`
  - Extract tensor data from GPU to CPU (NumPy array, complex128)

- `get_all_tensors_info(state) -> List[TensorInfo]`
  - Get metadata for all tensors in the network

### `TensorInfo`

Tensor metadata structure:

- `shape: List[int]` - Tensor dimensions (e.g., [2, 2] for single-qubit gate)
- `total_elements: int` - Total number of elements
- `size_bytes: int` - Size in bytes
- `dtype: str` - Data type (usually "complex128")
- `device_ptr: int` - GPU device pointer (for debugging)

## Testing

```bash
# Run quick test
./RUN_TESTS.sh simple

# Or run specific test
python scripts/test_bridge_simple.py

# Run all tests
./RUN_TESTS.sh all
```

## Current Limitations

1. **NumPy Copy Method**: Currently uses `cudaMemcpy` from device to host
   - Simple and reliable
   - Has memory copy overhead
   - Suitable for testing and small-scale data

2. **Future Optimization**: Planned DLPack support
   - Zero-copy transfer
   - Direct GPU operations
   - Higher efficiency

## Roadmap

1. ✅ Create basic pybind11 interface
2. ✅ Test NumPy copy method
3. ⏳ Verify PyTorch integration
4. ⏳ Implement DLPack zero-copy transfer
5. ⏳ Support tensor contraction
6. ⏳ Support custom tensor network operations

## Troubleshooting

### Module Import Failed

```
ImportError: cannot import name 'formotensor_bridge'
```

**Solution**: Make sure you have run `./REBUILD.sh` to build and install the module.

### Backend Not Supported

```
RuntimeError: State does not support tensor network extraction
```

**Solution**: Ensure you're using a tensornet backend:
```python
cudaq.set_target("tensornet")
```

### CUDA Errors

If you encounter CUDA-related errors, check:
- CUDA version compatibility
- Sufficient GPU memory
- `LD_LIBRARY_PATH` is correctly set

## Documentation

For complete documentation, see:
- **[Main Guide](../TENSORNET_EXTRACTION.md)** - Complete usage guide
- **[API Reference](../docs/FORMOTENSOR_BRIDGE_API.md)** - Detailed API documentation
- **[Examples](../scripts/)** - Example scripts and tools

