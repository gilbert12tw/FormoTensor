#!/usr/bin/env bash

set -euo pipefail

echo "==== FormoTensor Diagnostics ===="
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "User: ${USER:-unknown}"
echo

echo "[Environment]"
echo "CUDA_QUANTUM_PATH=${CUDA_QUANTUM_PATH:-unset}"
echo "CONDA_PREFIX=${CONDA_PREFIX:-unset}"
echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-unset}"
echo

if [[ -z "${CUDA_QUANTUM_PATH:-}" ]]; then
  echo "CUDA_QUANTUM_PATH is not set. Aborting." >&2
  exit 1
fi

echo "[NVQIR paths]"
echo "NVQIR_DIR=$CUDA_QUANTUM_PATH/lib/cmake/nvqir"
echo

echo "[Plugins in lib]"
ls -l "$CUDA_QUANTUM_PATH/lib" | grep -E "libnvqir-(formotensor|tensornet)" || true
echo

echo "[Configs in share/nvqir/simulators]"
if [[ -d "$CUDA_QUANTUM_PATH/share/nvqir/simulators" ]]; then
  ls -l "$CUDA_QUANTUM_PATH/share/nvqir/simulators" | grep -E "formotensor|tensornet" || true
else
  echo "No share/nvqir/simulators directory."
fi
echo

echo "[Configs in targets]"
if [[ -d "$CUDA_QUANTUM_PATH/targets" ]]; then
  ls -l "$CUDA_QUANTUM_PATH/targets" | grep -E "formotensor|tensornet" || true
else
  echo "No targets directory."
fi
echo

echo "[YAML: formotensor.yml (share)]"
if [[ -f "$CUDA_QUANTUM_PATH/share/nvqir/simulators/formotensor.yml" ]]; then
  sed -n '1,200p' "$CUDA_QUANTUM_PATH/share/nvqir/simulators/formotensor.yml" || true
else
  echo "Not found."
fi
echo

echo "[YAML: formotensor.yml (targets)]"
if [[ -f "$CUDA_QUANTUM_PATH/targets/formotensor.yml" ]]; then
  sed -n '1,200p' "$CUDA_QUANTUM_PATH/targets/formotensor.yml" || true
else
  echo "Not found."
fi
echo

echo "[Symbols in libnvqir-formotensor.so]"
if [[ -f "$CUDA_QUANTUM_PATH/lib/libnvqir-formotensor.so" ]]; then
  nm -D "$CUDA_QUANTUM_PATH/lib/libnvqir-formotensor.so" | grep getCircuitSimulator || true
else
  echo "Library not found."
fi
echo

echo "[ldd -r libnvqir-formotensor.so]"
if [[ -f "$CUDA_QUANTUM_PATH/lib/libnvqir-formotensor.so" ]]; then
  ldd -r "$CUDA_QUANTUM_PATH/lib/libnvqir-formotensor.so" || true
else
  echo "Library not found."
fi
echo

echo "[Python targets + set_target check]"
PYTHON=${PYTHON:-python}
"$PYTHON" - <<'PY'
import os, sys
import traceback
import cudaq

print("CUDA-Q version:", getattr(cudaq, "__version__", "unknown"))
print("Targets:")
print([t.name for t in cudaq.get_targets()])

def try_set(name: str):
    print(f"\n-- set_target({name})")
    try:
        cudaq.set_target(name)
        print("OK")
    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()

for tgt in ["formotensor", "formotensor-mps", "formotensor-fp32", "formotensor-mps-fp32"]:
    try_set(tgt)
PY
echo

echo "==== End Diagnostics ===="




