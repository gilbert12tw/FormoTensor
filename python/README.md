# FormoTensor Python Bridge

簡單的 pybind11 接口，用於從 CUDA-Q 電路中提取 Tensor Network。

## 功能

1. **提取 Tensor Network 資訊**：從 CUDA-Q 電路中獲取 tensor 的 metadata
2. **提取 Tensor 數據**：將 GPU 上的 tensor 數據複製到 NumPy array（使用 NumPy copy 方法）
3. **PyTorch 對接**：輕鬆轉換為 PyTorch tensor 進行進一步操作
4. **DLPack 優化空間**：未來可以替換為 zero-copy DLPack 傳輸

## 編譯和安裝

```bash
# 在 FormoTensor 根目錄
cd build
cmake .. -GNinja
ninja install
```

這會將 `formotensor_bridge` 模塊安裝到您的 Python 環境中。

## 使用範例

```python
import cudaq
import formotensor_bridge as ftb
import numpy as np
import torch

# 1. 設定 FormoTensor backend
cudaq.set_target("tensornet")

# 2. 定義並執行量子電路
@cudaq.kernel
def my_circuit():
    q = cudaq.qvector(3)
    h(q[0])
    cx(q[0], q[1])
    cx(q[1], q[2])

result = cudaq.sample(my_circuit, shots_count=100)

# 3. 提取 Tensor Network 資訊
num_tensors = ftb.TensorNetworkExtractor.get_num_tensors()
num_qubits = ftb.TensorNetworkExtractor.get_num_qubits()

print(f"Qubits: {num_qubits}, Tensors: {num_tensors}")

# 4. 提取單個 tensor 數據（NumPy copy）
tensor_data = ftb.TensorNetworkExtractor.extract_tensor_data(0)
print(f"Tensor shape: {tensor_data.shape}")

# 5. 轉換為 PyTorch（在 GPU 上）
torch_tensor = torch.from_numpy(tensor_data.copy()).to('cuda')
print(f"PyTorch tensor on: {torch_tensor.device}")

# 6. 在 PyTorch 中進行操作
modified_tensor = torch_tensor * 0.5  # 簡單的縮放操作

# 7. 轉回 NumPy（如果需要）
result_numpy = modified_tensor.cpu().numpy()
```

## API 參考

### `TensorNetworkExtractor`

#### 靜態方法

- `get_num_tensors() -> int`
  - 獲取當前 tensor network 中的 tensor 數量

- `get_num_qubits() -> int`
  - 獲取當前電路中的 qubit 數量

- `extract_tensor_info(kernel_name: str = "") -> List[TensorInfo]`
  - 提取所有 tensor 的 metadata 資訊

- `extract_tensor_data(tensor_idx: int, kernel_name: str = "") -> np.ndarray`
  - 提取指定 tensor 的數據（複製到 host memory）
  - 返回 NumPy array（complex128）

### `TensorInfo`

Tensor 的 metadata 結構：

- `target_qubits: List[int]` - 目標 qubit 索引
- `control_qubits: List[int]` - 控制 qubit 索引
- `is_adjoint: bool` - 是否為伴隨操作
- `is_unitary: bool` - 是否為單一操作
- `data_size: int` - 數據大小（bytes）
- `device_ptr: int` - GPU device pointer（用於調試）

## 測試

```bash
# 運行測試腳本
python python/test_bridge.py
```

## 目前限制

1. **NumPy Copy 方法**：目前使用 `cudaMemcpy` 從 device 複製到 host
   - 簡單、可靠
   - 有記憶體拷貝開銷
   - 適合測試和小規模數據

2. **未來優化**：計劃使用 DLPack
   - Zero-copy 傳輸
   - 直接在 GPU 上操作
   - 更高效率

## 下一步

1. ✅ 創建基本的 pybind11 接口
2. ✅ 測試 NumPy copy 方法
3. ✅ 驗證 PyTorch 對接
4. ⏳ 實作 DLPack zero-copy 傳輸
5. ⏳ 支持 tensor contraction
6. ⏳ 支持自定義 tensor network 操作

## 疑難排解

### 模塊導入失敗

```
ImportError: cannot import name 'formotensor_bridge'
```

**解決方案**：確保已經執行 `ninja install`

### 找不到 simulator

```
RuntimeError: Current backend is not a TensorNet simulator
```

**解決方案**：確保使用 `cudaq.set_target("tensornet")` 或其他 FormoTensor backend

### CUDA 錯誤

如果遇到 CUDA 相關錯誤，檢查：
- CUDA 版本兼容性
- GPU 記憶體是否足夠
- 是否正確設置 `LD_LIBRARY_PATH`

