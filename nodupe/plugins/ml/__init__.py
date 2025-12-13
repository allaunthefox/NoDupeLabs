"""NoDupeLabs ML Plugins - Machine Learning Backends

This module provides ML backend implementations for embedding generation
and other machine learning tasks with graceful degradation.
"""

from typing import List, Optional, Any
import numpy as np
import logging
from abc import ABC, abstractmethod

# Configure logging
logger = logging.getLogger(__name__)

class MLBackend(ABC):
    """Abstract base class for ML backends"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available"""
        pass

    @abstractmethod
    def generate_embeddings(self, data: List[Any]) -> List[List[float]]:
        """Generate embeddings for input data"""
        pass

    @abstractmethod
    def get_embedding_dimensions(self) -> int:
        """Get the dimensionality of embeddings produced by this backend"""
        pass

class CPUBackend(MLBackend):
    """CPU-based ML backend using pure NumPy (always available)"""

    def __init__(self):
        self.dimensions = 128  # Default embedding dimensions

    def is_available(self) -> bool:
        """This backend is always available"""
        return True

    def generate_embeddings(self, data: List[Any]) -> List[List[float]]:
        """
        Generate simple embeddings using NumPy
        This is a placeholder implementation that creates random embeddings
        """
        try:
            # Create random embeddings for demonstration
            embeddings = []
            for item in data:
                # Simple hash-based embedding for demonstration
                if isinstance(item, str):
                    # Convert string to numerical representation
                    embedding = np.random.randn(self.dimensions).tolist()
                elif isinstance(item, (list, np.ndarray)):
                    # For array-like data, create embedding based on content
                    embedding = np.random.randn(self.dimensions).tolist()
                else:
                    # Fallback for other types
                    embedding = np.random.randn(self.dimensions).tolist()
                embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings with CPU backend: {e}")
            # Return empty embeddings on error
            return [[] for _ in data]

    def get_embedding_dimensions(self) -> int:
        """Get embedding dimensionality"""
        return self.dimensions

class ONNXBackend(MLBackend):
    """ONNX Runtime backend for ML inference"""

    def __init__(self, model_path: Optional[str] = None):
        self.dimensions = 128
        self.model_path = model_path
        self._available = False
        self._model = None

        try:
            # Try to import ONNX runtime
            import onnxruntime as ort

            # Try to load model if path provided
            if model_path:
                self._model = ort.InferenceSession(model_path)
                self._available = True
                logger.info(f"ONNX backend loaded model from {model_path}")
            else:
                logger.warning("ONNX backend: no model path provided")
        except ImportError:
            logger.warning("ONNX runtime not available, falling back to CPU backend")
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")

    def is_available(self) -> bool:
        """Check if ONNX backend is available"""
        return self._available

    def generate_embeddings(self, data: List[Any]) -> List[List[float]]:
        """Generate embeddings using ONNX model"""
        if not self.is_available():
            logger.warning("ONNX backend not available, using CPU fallback")
            cpu_backend = CPUBackend()
            return cpu_backend.generate_embeddings(data)

        try:
            # Placeholder: actual implementation would use ONNX model
            embeddings = []
            for item in data:
                # Convert data to format expected by ONNX model
                # This is a placeholder - actual implementation would preprocess data
                embedding = np.random.randn(self.dimensions).tolist()
                embeddings.append(embedding)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings with ONNX backend: {e}")
            # Fallback to CPU backend
            cpu_backend = CPUBackend()
            return cpu_backend.generate_embeddings(data)

    def get_embedding_dimensions(self) -> int:
        """Get embedding dimensionality"""
        return self.dimensions

def create_ml_backend(backend_type: str = "auto", **kwargs) -> MLBackend:
    """
    Create an ML backend instance with graceful degradation

    Args:
        backend_type: Type of backend ('auto', 'cpu', 'onnx')
        **kwargs: Additional arguments for backend creation

    Returns:
        MLBackend instance
    """
    backend_type = backend_type.lower()

    if backend_type == "auto":
        # Try ONNX first, fallback to CPU
        try:
            onnx_backend = ONNXBackend(kwargs.get('model_path'))
            if onnx_backend.is_available():
                logger.info("Using ONNX backend")
                return onnx_backend
        except Exception:
            pass

        # Fallback to CPU
        logger.info("Using CPU backend (fallback)")
        return CPUBackend()

    elif backend_type == "onnx":
        return ONNXBackend(kwargs.get('model_path'))

    elif backend_type == "cpu":
        return CPUBackend()

    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

# Module-level backend instance (lazy initialization)
ML_BACKEND: Optional[MLBackend] = None

def get_ml_backend() -> MLBackend:
    """Get the global ML backend instance"""
    global ML_BACKEND
    if ML_BACKEND is None:
        ML_BACKEND = create_ml_backend()
    return ML_BACKEND

# Initialize backend on import
get_ml_backend()

__all__ = ['MLBackend', 'CPUBackend', 'ONNXBackend', 'create_ml_backend', 'get_ml_backend']
