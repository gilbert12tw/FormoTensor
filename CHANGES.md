# FormoTensor 變更記錄

## Simulator 名稱統一更新

### 變更概述
將所有 simulator 名稱從 `tensornet` 系列更新為 `formotensor` 系列，以反映 FormoTensor 的增強功能。

### 更新的 Backend 名稱

| 原始名稱 | 新名稱 | 說明 |
|---------|--------|------|
| `tensornet` | `formotensor` | 增強的張量網路模擬器 (FP64) |
| `tensornet-mps` | `formotensor-mps` | 增強的 MPS 模擬器 (FP64) |
| `tensornet-fp32` | `formotensor-fp32` | 增強的張量網路模擬器 (FP32) |
| `tensornet-mps-fp32` | `formotensor-mps-fp32` | 增強的 MPS 模擬器 (FP32) |

### 修改的檔案

#### CMakeLists.txt
- 專案名稱：`CuTensorNetStandalone` → `FormoTensor`
- Build configuration 標題更新
- 所有 backend target 名稱更新
- 配置檔案名稱更新

#### 源碼檔案
- `src/simulator_tensornet_fp64_register.cpp`
  - `getCircuitSimulator_tensornet()` → `getCircuitSimulator_formotensor()`
  - 註冊名稱：`"tensornet"` → `"formotensor"`

- `src/simulator_tensornet_fp32_register.cpp`
  - `getCircuitSimulator_tensornet_fp32()` → `getCircuitSimulator_formotensor_fp32()`
  - 註冊名稱：`"tensornet-fp32"` → `"formotensor-fp32"`

- `src/simulator_mps_fp64_register.cpp`
  - `NVQIR_REGISTER_SIMULATOR(..., tensornet_mps)` → `NVQIR_REGISTER_SIMULATOR(..., formotensor_mps)`

- `src/simulator_mps_fp32_register.cpp`
  - `NVQIR_REGISTER_SIMULATOR(..., tensornet_mps_fp32)` → `NVQIR_REGISTER_SIMULATOR(..., formotensor_mps_fp32)`

- `src/simulator_tensornet.h`
  - Forward declarations 更新
  - `name()` 方法回傳值更新
  - Friend function declarations 更新

- `src/simulator_mps.h`
  - `name()` 方法回傳值更新

#### 文檔和腳本
- `README.md`
  - 專案標題和描述更新
  - Backend 表格更新
  - 使用範例更新
  - 測試指令更新
  - 專案結構更新

- `install_dependencies.sh`
  - 腳本標題更新
  - 環境名稱建議更新
  - 測試指令更新

#### 測試檔案
- 新建 `test_formotensor.py`
  - 全面的 backend 測試套件
  - 測試所有 formotensor backends
  - 包含電路測試、效能測試、錯誤報告

### 使用方式變更

#### 之前
```python
import cudaq
cudaq.set_target("tensornet")
```

#### 現在
```python
import cudaq
cudaq.set_target("formotensor")
```

### 編譯輸出變更
編譯後會產生以下檔案：
- `libnvqir-formotensor.so`
- `libnvqir-formotensor-mps.so`
- `libnvqir-formotensor-fp32.so`
- `libnvqir-formotensor-mps-fp32.so`
- `formotensor.yml`
- `formotensor-mps.yml`
- `formotensor-fp32.yml`
- `formotensor-mps-fp32.yml`

### 測試驗證
使用新的測試腳本驗證所有 backends：
```bash
python test_formotensor.py
```

### 向後相容性
⚠️ **注意**: 此更新不向後相容。所有使用舊 `tensornet` 名稱的程式碼都需要更新為新的 `formotensor` 名稱。
