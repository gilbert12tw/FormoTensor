/**
 * FormoTensor Python Bridge
 * Simple pybind11 interface to extract tensor network from CUDA-Q circuits
 * 
 * Note: This works with cudaq.State objects that have getTensor/getTensors methods
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <pybind11/complex.h>
#include <cuda_runtime.h>
#include <complex>
#include <vector>

namespace py = pybind11;

// Simplified tensor information structure
struct TensorInfo {
    std::vector<size_t> shape;      // Tensor dimensions
    size_t total_elements;           // Total number of elements
    size_t size_bytes;               // Size in bytes
    std::string dtype;               // Data type (e.g., "complex128")
    uint64_t device_ptr;             // Device pointer (for debugging)
    
    TensorInfo() : total_elements(0), size_bytes(0), device_ptr(0), dtype("unknown") {}
};

// Helper functions to work with Python State objects
// These functions use Python API to call methods on cudaq.State objects
class TensorNetworkHelper {
public:
    // Get number of qubits from a cudaq.State object (via Python API)
    static size_t get_num_qubits(py::object state) {
        if (!py::hasattr(state, "num_qubits")) {
            throw std::runtime_error("State object does not have 'num_qubits' method");
        }
        return state.attr("num_qubits")().cast<size_t>();
    }
    
    // Check if state has tensor network representation
    static bool has_tensors(py::object state) {
        return py::hasattr(state, "getTensors") || py::hasattr(state, "getTensor");
    }
    
    // Get tensor at specific index (via Python API)
    static TensorInfo get_tensor_info(py::object state, size_t idx) {
        if (!py::hasattr(state, "getTensor")) {
            throw std::runtime_error("State object does not support getTensor()");
        }
        
        TensorInfo info;
        
        try {
            // Call Python method: state.getTensor(idx)
            py::object tensor_obj = state.attr("getTensor")(idx);
            
            // Try to get tensor properties
            if (py::hasattr(tensor_obj, "extents")) {
                auto extents = tensor_obj.attr("extents").cast<std::vector<size_t>>();
                info.shape = extents;
                
                // Calculate total size
                info.total_elements = 1;
                for (auto dim : extents) {
                    info.total_elements *= dim;
                }
                info.size_bytes = info.total_elements * sizeof(std::complex<double>);
                info.dtype = "complex128";
            }
            
            // Try to get device pointer
            if (py::hasattr(tensor_obj, "data")) {
                // This would need proper casting, for now just mark as available
                info.device_ptr = 1;  // Non-zero means data is available
            }
            
        } catch (const std::exception& e) {
            throw std::runtime_error(
                std::string("Failed to get tensor info: ") + e.what()
            );
        }
        
        return info;
    }
    
    // Extract tensor data to NumPy array
    static py::array_t<std::complex<double>> extract_tensor_data(
        py::object state, size_t idx) {
        
        if (!py::hasattr(state, "getTensor")) {
            throw std::runtime_error("State object does not support getTensor()");
        }
        
        try {
            // Get tensor object
            py::object tensor_obj = state.attr("getTensor")(idx);
            
            // Try to access data directly if available
            if (py::hasattr(tensor_obj, "data") && py::hasattr(tensor_obj, "extents")) {
                auto extents = tensor_obj.attr("extents").cast<std::vector<size_t>>();
                
                // Get the device pointer
                // Note: 'data' is a bound method in CUDA-Q Tensor objects
                void* device_ptr = nullptr;
                
                try {
                    // First, try calling it as a method (most common case)
                    py::object data_result = tensor_obj.attr("data")();
                    
                    // The result should be a pointer (integer) or capsule
                    if (py::isinstance<py::int_>(data_result)) {
                        // It's an integer representation of the pointer
                        device_ptr = reinterpret_cast<void*>(data_result.cast<uintptr_t>());
                    } else {
                        // Try direct cast
                        device_ptr = data_result.cast<void*>();
                    }
                } catch (const py::error_already_set&) {
                    // If calling fails, try accessing as property
                    py::object data_obj = tensor_obj.attr("data");
                    device_ptr = data_obj.cast<void*>();
                }
                
                // Calculate total size
                size_t total_size = 1;
                for (auto dim : extents) {
                    total_size *= dim;
                }
                
                // Allocate host memory
                std::vector<std::complex<double>> host_data(total_size);
                
                // Copy from device to host
                cudaError_t err = cudaMemcpy(
                    host_data.data(),
                    device_ptr,
                    total_size * sizeof(std::complex<double>),
                    cudaMemcpyDeviceToHost
                );
                
                if (err != cudaSuccess) {
                    throw std::runtime_error(
                        "CUDA memcpy failed: " + std::string(cudaGetErrorString(err))
                    );
                }
                
                // Create NumPy array
                std::vector<ssize_t> shape(extents.begin(), extents.end());
                py::array_t<std::complex<double>> result(shape);
                std::memcpy(result.mutable_data(), host_data.data(),
                           total_size * sizeof(std::complex<double>));
                return result;
            } else {
                throw std::runtime_error(
                    "Tensor object does not expose 'data' or 'extents' attributes"
                );
            }
            
        } catch (const std::exception& e) {
            throw std::runtime_error(
                std::string("Failed to extract tensor data: ") + e.what()
            );
        }
    }
    
    // Get all tensors info (if getTensors is available)
    static std::vector<TensorInfo> get_all_tensors_info(py::object state) {
        std::vector<TensorInfo> tensors;
        
        if (py::hasattr(state, "getTensors")) {
            try {
                py::object tensors_obj = state.attr("getTensors")();
                
                // Try to iterate
                if (py::hasattr(tensors_obj, "__len__")) {
                    size_t num_tensors = py::len(tensors_obj);
                    
                    for (size_t i = 0; i < num_tensors; ++i) {
                        try {
                            TensorInfo info = get_tensor_info(state, i);
                            tensors.push_back(info);
                        } catch (...) {
                            // Skip tensors that fail
                            continue;
                        }
                    }
                }
            } catch (const std::exception& e) {
                throw std::runtime_error(
                    std::string("Failed to get tensors: ") + e.what()
                );
            }
        }
        
        return tensors;
    }
};

// Python module definition
PYBIND11_MODULE(formotensor_bridge, m) {
    m.doc() = "FormoTensor Python Bridge - Extract Tensor Networks from CUDA-Q\n\n"
              "Works with cudaq.State objects that have getTensor/getTensors methods.";
    
    // TensorInfo structure
    py::class_<TensorInfo>(m, "TensorInfo")
        .def(py::init<>())
        .def_readonly("shape", &TensorInfo::shape,
                     "Tensor shape (dimensions)")
        .def_readonly("total_elements", &TensorInfo::total_elements,
                     "Total number of elements")
        .def_readonly("size_bytes", &TensorInfo::size_bytes,
                     "Size in bytes")
        .def_readonly("dtype", &TensorInfo::dtype,
                     "Data type (e.g., 'complex128')")
        .def_readonly("device_ptr", &TensorInfo::device_ptr,
                     "Device pointer (0 if not available)")
        .def("__repr__", [](const TensorInfo& info) {
            std::string shape_str = "[";
            for (size_t i = 0; i < info.shape.size(); ++i) {
                if (i > 0) shape_str += ", ";
                shape_str += std::to_string(info.shape[i]);
            }
            shape_str += "]";
            
            return "<TensorInfo: shape=" + shape_str + 
                   ", elements=" + std::to_string(info.total_elements) +
                   ", dtype=" + info.dtype + ">";
        });
    
    // Main helper class (works with Python cudaq.State objects)
    py::class_<TensorNetworkHelper>(m, "TensorNetworkHelper")
        .def_static("get_num_qubits", &TensorNetworkHelper::get_num_qubits,
                   "Get number of qubits from a cudaq.State object",
                   py::arg("state"))
        .def_static("has_tensors", &TensorNetworkHelper::has_tensors,
                   "Check if state has tensor network methods (getTensor/getTensors)",
                   py::arg("state"))
        .def_static("get_tensor_info", &TensorNetworkHelper::get_tensor_info,
                   "Get information about a specific tensor",
                   py::arg("state"), py::arg("tensor_idx"))
        .def_static("extract_tensor_data", &TensorNetworkHelper::extract_tensor_data,
                   "Extract tensor data as NumPy array (copies from GPU to CPU)",
                   py::arg("state"), py::arg("tensor_idx"))
        .def_static("get_all_tensors_info", &TensorNetworkHelper::get_all_tensors_info,
                   "Get information about all tensors in the network",
                   py::arg("state"));
    
    // Version info
    m.attr("__version__") = "0.2.0";
}

