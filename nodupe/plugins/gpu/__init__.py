"""NoDupeLabs GPU Plugins - Hardware Acceleration Backends

This module provides GPU acceleration backends for various compute-intensive
operations with graceful degradation to CPU implementations.
"""

from typing import List, Optional, Any, Dict
import numpy as np
import logging
from abc import ABC, abstractmethod

# Configure logging
logger = logging.getLogger(__name__)

class GPUBackend(ABC):
    """Abstract base class for GPU backends"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available"""
        pass

    @abstractmethod
    def compute_embeddings(self, data: List[Any]) -> List[List[float]]:
        """Compute embeddings using GPU acceleration"""
        pass

    @abstractmethod
    def matrix_multiply(self, a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Perform matrix multiplication using GPU"""
        pass

    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """Get information about the GPU device"""
        pass

class CPUFallbackBackend(GPUBackend):
    """CPU fallback backend (always available)"""

    def __init__(self):
        self.device_info = {
            'type': 'cpu',
            'name': 'CPU Fallback',
            'memory': 'N/A',
            'compute_units': 'N/A'
        }

    def is_available(self) -> bool:
        """CPU backend is always available"""
        return True

    def compute_embeddings(self, data: List[Any]) -> List[List[float]]:
        """Compute embeddings using CPU"""
        try:
            embeddings = []
            for item in data:
                # Simple CPU-based embedding computation
                if isinstance(item, (list, np.ndarray)):
                    # Convert to numpy array and normalize
                    arr = np.array(item, dtype=np.float32)
                    embedding = (arr / np.linalg.norm(arr)).tolist()
                else:
                    # Fallback for other types
                    embedding = np.random.randn(128).tolist()
                embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"Error in CPU embedding computation: {e}")
            return [[] for _ in data]

    def matrix_multiply(self, a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Matrix multiplication using NumPy"""
        try:
            a_arr = np.array(a, dtype=np.float32)
            b_arr = np.array(b, dtype=np.float32)
            result = np.matmul(a_arr, b_arr)
            return result.tolist()
        except Exception as e:
            logger.error(f"Error in CPU matrix multiplication: {e}")
            return []

    def get_device_info(self) -> Dict[str, Any]:
        """Get CPU device information"""
        return self.device_info

class CUDABackend(GPUBackend):
    """NVIDIA CUDA backend using PyTorch"""

    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self._available = False
        self.device_info = {}

        try:
            # Try to import PyTorch and check CUDA availability
            import torch

            if torch.cuda.is_available():
                self._available = True
                self.device = torch.device(f'cuda:{device_id}')
                self.device_info = {
                    'type': 'cuda',
                    'name': torch.cuda.get_device_name(device_id),
                    'memory': f"{torch.cuda.get_device_properties(device_id).total_memory / 1024**3:.2f} GB",
                    'compute_units': torch.cuda.get_device_properties(device_id).multi_processor_count
                }
                logger.info(f"CUDA backend initialized on device {device_id}: {self.device_info['name']}")
            else:
                logger.warning("CUDA not available")
        except ImportError:
            logger.warning("PyTorch not available for CUDA backend")
        except Exception as e:
            logger.error(f"Failed to initialize CUDA backend: {e}")

    def is_available(self) -> bool:
        """Check if CUDA backend is available"""
        return self._available

    def compute_embeddings(self, data: List[Any]) -> List[List[float]]:
        """Compute embeddings using CUDA"""
        if not self.is_available():
            logger.warning("CUDA backend not available, using CPU fallback")
            fallback = CPUFallbackBackend()
            return fallback.compute_embeddings(data)

        try:
            import torch

            embeddings = []
            for item in data:
                if isinstance(item, (list, np.ndarray)):
                    # Convert to tensor and move to GPU
                    tensor = torch.tensor(item, dtype=torch.float32).to(self.device)
                    # Simple normalization on GPU
                    embedding = tensor / torch.norm(tensor)
                    embeddings.append(embedding.cpu().numpy().tolist())
                else:
                    # Fallback
                    embedding = np.random.randn(128).tolist()
                    embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"Error in CUDA embedding computation: {e}")
            fallback = CPUFallbackBackend()
            return fallback.compute_embeddings(data)

    def matrix_multiply(self, a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Matrix multiplication using CUDA"""
        if not self.is_available():
            logger.warning("CUDA backend not available, using CPU fallback")
            fallback = CPUFallbackBackend()
            return fallback.matrix_multiply(a, b)

        try:
            import torch

            a_tensor = torch.tensor(a, dtype=torch.float32).to(self.device)
            b_tensor = torch.tensor(b, dtype=torch.float32).to(self.device)
            result = torch.matmul(a_tensor, b_tensor)
            return result.cpu().numpy().tolist()
        except Exception as e:
            logger.error(f"Error in CUDA matrix multiplication: {e}")
            fallback = CPUFallbackBackend()
            return fallback.matrix_multiply(a, b)

    def get_device_info(self) -> Dict[str, Any]:
        """Get CUDA device information"""
        return self.device_info

class MetalBackend(GPUBackend):
    """Apple Metal backend for M1/M2/M3 GPUs"""

    def __init__(self):
        self._available = False
        self.device_info = {}

        try:
            # Try to import PyTorch and check Metal availability
            import torch

            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self._available = True
                self.device = torch.device('mps')
                self.device_info = {
                    'type': 'metal',
                    'name': 'Apple Metal (M1/M2/M3)',
                    'memory': 'Integrated',
                    'compute_units': 'Multiple'
                }
                logger.info("Metal backend initialized for Apple Silicon")
            else:
                logger.warning("Metal not available")
        except ImportError:
            logger.warning("PyTorch not available for Metal backend")
        except Exception as e:
            logger.error(f"Failed to initialize Metal backend: {e}")

    def is_available(self) -> bool:
        """Check if Metal backend is available"""
        return self._available

    def compute_embeddings(self, data: List[Any]) -> List[List[float]]:
        """Compute embeddings using Metal"""
        if not self.is_available():
            logger.warning("Metal backend not available, using CPU fallback")
            fallback = CPUFallbackBackend()
            return fallback.compute_embeddings(data)

        try:
            import torch

            embeddings = []
            for item in data:
                if isinstance(item, (list, np.ndarray)):
                    tensor = torch.tensor(item, dtype=torch.float32).to(self.device)
                    embedding = tensor / torch.norm(tensor)
                    embeddings.append(embedding.cpu().numpy().tolist())
                else:
                    embedding = np.random.randn(128).tolist()
                    embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"Error in Metal embedding computation: {e}")
            fallback = CPUFallbackBackend()
            return fallback.compute_embeddings(data)

    def matrix_multiply(self, a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Matrix multiplication using Metal"""
        if not self.is_available():
            logger.warning("Metal backend not available, using CPU fallback")
            fallback = CPUFallbackBackend()
            return fallback.matrix_multiply(a, b)

        try:
            import torch

            a_tensor = torch.tensor(a, dtype=torch.float32).to(self.device)
            b_tensor = torch.tensor(b, dtype=torch.float32).to(self.device)
            result = torch.matmul(a_tensor, b_tensor)
            return result.cpu().numpy().tolist()
        except Exception as e:
            logger.error(f"Error in Metal matrix multiplication: {e}")
            fallback = CPUFallbackBackend()
            return fallback.matrix_multiply(a, b)

    def get_device_info(self) -> Dict[str, Any]:
        """Get Metal device information"""
        return self.device_info

def create_gpu_backend(backend_type: str = "auto", **kwargs) -> GPUBackend:
    """
    Create a GPU backend instance with graceful degradation

    Args:
        backend_type: Type of backend ('auto', 'cpu', 'cuda', 'metal', 'opencl', 'vulkan')
        **kwargs: Additional arguments for backend creation

    Returns:
        GPUBackend instance
    """
    backend_type = backend_type.lower()

    if backend_type == "auto":
        # Try backends in priority order
        backends_to_try = ['cuda', 'metal', 'opencl', 'vulkan']

        for btype in backends_to_try:
            try:
                if btype == 'cuda':
                    backend = CUDABackend(kwargs.get('device_id', 0))
                elif btype == 'metal':
                    backend = MetalBackend()
                # elif btype == 'opencl':
                #     backend = OpenCLBackend()
                # elif btype == 'vulkan':
                #     backend = VulkanBackend()

                if backend.is_available():
                    logger.info(f"Using {btype.upper()} backend")
                    return backend
            except Exception:
                continue

        # Fallback to CPU
        logger.info("Using CPU backend (GPU fallback)")
        return CPUFallbackBackend()

    elif backend_type == "cuda":
        return CUDABackend(kwargs.get('device_id', 0))

    elif backend_type == "metal":
        return MetalBackend()

    elif backend_type == "cpu":
        return CPUFallbackBackend()

    else:
        raise ValueError(f"Unknown GPU backend type: {backend_type}")

# Module-level backend instance
GPU_BACKEND: Optional[GPUBackend] = None

def get_gpu_backend() -> GPUBackend:
    """Get the global GPU backend instance"""
    global GPU_BACKEND
    if GPU_BACKEND is None:
        GPU_BACKEND = create_gpu_backend()
    return GPU_BACKEND

# Initialize backend on import
get_gpu_backend()

__all__ = [
    'GPUBackend', 'CPUFallbackBackend', 'CUDABackend', 'MetalBackend',
    'create_gpu_backend', 'get_gpu_backend'
]
