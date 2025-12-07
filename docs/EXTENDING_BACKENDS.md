# Extending Backends Guide

**Version:** 1.0
**Last Updated:** 2025-12-05

---

## Table of Contents

1. [Introduction](#introduction)
2. [AI Backends](#ai-backends)
3. [Similarity Backends](#similarity-backends)
4. [Backend Selection Logic](#backend-selection-logic)
5. [Testing Backends](#testing-backends)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

---

## Introduction

NoDupe Labs uses a **pluggable backend system** for two main subsystems:

1. **AI Backends** - Compute image/video embeddings for semantic similarity
2. **Similarity Backends** - Perform vector similarity search (find near-duplicates)

Both use the **Factory Pattern** to enable:

- Runtime backend selection
- Graceful degradation (fallback to simpler implementations)
- Easy extension without modifying core code

### Architecture

```text
┌─────────────────────────────────────────┐
│         Application Code                │
│  (Uses abstract interface)              │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Backend Factory                    │
│  (Selects implementation at runtime)    │
└──────┬───────────────┬──────────────────┘
       │               │
┌──────▼──────┐  ┌─────▼────────┐
│ AI Backend  │  │ Similarity   │
│   System    │  │  System      │
└──────┬──────┘  └─────┬────────┘
       │               │
   ┌───▼───┐      ┌────▼─────┐
   │ ONNX  │      │  FAISS   │
   │ (GPU) │      │ (Fast)   │
   └───────┘      └──────────┘
       │               │
   ┌───▼───┐      ┌────▼────────┐
   │  CPU  │      │ Brute-force │
   │(Slow) │      │  (Simple)   │
   └───────┘      └─────────────┘
```

---

## AI Backends

AI backends compute **perceptual embeddings** for images and videos. These embeddings are used to find visually similar files.

### Base Interface

All AI backends inherit from `BaseBackend`:

```python
# nodupe/ai/backends/base.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import numpy as np

class BaseBackend(ABC):
    """Abstract base class for AI backends.

    Backends compute perceptual embeddings for images/videos
    to enable semantic similarity search.
    """

    @abstractmethod
    def compute_embedding(self, file_path: Path) -> Optional[np.ndarray]:
        """Compute embedding vector for a file.

        Args:
            file_path: Path to image or video file

        Returns:
            Embedding vector (numpy array) or None if failed

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format unsupported
        """
        pass

    @abstractmethod
    def get_embedding_dim(self) -> int:
        """Get dimension of embedding vectors.

        Returns:
            Embedding dimension (e.g., 512, 1024, 2048)
        """
        pass

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(dim={self.get_embedding_dim()})"
```

### Creating a New AI Backend

#### Step 1: Create Backend File

```python
# nodupe/ai/backends/my_backend.py
"""My custom AI backend implementation."""
from pathlib import Path
from typing import Optional
import numpy as np
from .base import BaseBackend

class MyBackend(BaseBackend):
    """Custom AI backend using MyModel.

    This backend uses MyModel to compute embeddings for images/videos.
    It requires the 'mymodel' package to be installed.

    Attributes:
        model: Loaded model instance
        dim: Embedding dimension

    Example:
        >>> backend = MyBackend()
        >>> embedding = backend.compute_embedding(Path('image.jpg'))
        >>> embedding.shape
        (512,)
    """

    def __init__(self, model_path: Optional[str] = None):
        """Initialize backend.

        Args:
            model_path: Optional path to model weights
        """
        try:
            import mymodel  # Check dependency
        except ImportError:
            raise ImportError(
                "MyBackend requires 'mymodel' package. "
                "Install with: pip install mymodel"
            )

        # Load model
        self.model = mymodel.load_model(model_path)
        self.dim = 512  # Model-specific dimension

    def compute_embedding(self, file_path: Path) -> Optional[np.ndarray]:
        """Compute embedding for an image/video.

        Args:
            file_path: Path to file

        Returns:
            Embedding vector (512-dim) or None if failed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Load and preprocess
            image = self._load_image(file_path)
            if image is None:
                return None

            # Compute embedding
            embedding = self.model.encode(image)

            # Normalize (optional but recommended)
            embedding = embedding / np.linalg.norm(embedding)

            return embedding

        except Exception as e:
            # Log error but don't crash
            print(f"[MyBackend] Failed to compute embedding: {e}")
            return None

    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.dim

    def _load_image(self, file_path: Path):
        """Load and preprocess image."""
        # Implementation depends on your model
        pass
```

#### Step 2: Add to Backend Selection

Update the `choose_backend()` function:

```python
# nodupe/ai/backends/__init__.py
from typing import Optional
from .base import BaseBackend
from .onnx_backend import ONNXBackend
from .cpu_backend import CPUBackend
from .my_backend import MyBackend  # Import

def choose_backend(preference: Optional[str] = None) -> BaseBackend:
    """Select best available AI backend.

    Args:
        preference: Optional backend name ('onnx', 'cpu', 'my')

    Returns:
        Best available backend instance

    Raises:
        RuntimeError: If no backends available
    """
    # User-specified backend
    if preference == 'my':
        try:
            return MyBackend()
        except ImportError as e:
            print(f"[AI] MyBackend unavailable: {e}")

    # Auto-selection (best to worst)
    backends = [
        ('my', MyBackend),      # Try custom backend first
        ('onnx', ONNXBackend),  # Then ONNX (GPU/CPU accelerated)
        ('cpu', CPUBackend),    # Finally pure CPU
    ]

    for name, backend_class in backends:
        try:
            backend = backend_class()
            print(f"[AI] Using {name} backend")
            return backend
        except ImportError:
            continue  # Try next backend

    raise RuntimeError("No AI backends available")
```

#### Step 3: Test Backend

```python
# tests/test_my_backend.py
import pytest
from pathlib import Path
import numpy as np
from nodupe.ai.backends.my_backend import MyBackend

@pytest.fixture
def backend():
    """Create backend instance."""
    try:
        return MyBackend()
    except ImportError:
        pytest.skip("MyBackend dependencies not available")

def test_embedding_dimension(backend):
    """Test that embedding dimension is correct."""
    assert backend.get_embedding_dim() == 512

def test_compute_embedding(backend, tmp_path):
    """Test embedding computation."""
    # Create test image
    test_image = tmp_path / "test.jpg"
    # ... create valid image file

    # Compute embedding
    embedding = backend.compute_embedding(test_image)

    # Verify
    assert embedding is not None
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (512,)
    assert np.isfinite(embedding).all()

def test_file_not_found(backend):
    """Test handling of missing files."""
    with pytest.raises(FileNotFoundError):
        backend.compute_embedding(Path("nonexistent.jpg"))
```

---

## Similarity Backends

Similarity backends perform **vector similarity search** to find near-duplicate files based on embeddings.

### Base Interface

```python
# nodupe/similarity/backends/base.py (conceptual)
from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np

class SimilarityBackend(ABC):
    """Abstract base for similarity search backends."""

    @abstractmethod
    def add(self, ids: List[str], vectors: List[np.ndarray]) -> None:
        """Add vectors to index.

        Args:
            ids: File paths or identifiers
            vectors: Embedding vectors
        """
        pass

    @abstractmethod
    def search(
        self,
        query_vectors: List[np.ndarray],
        k: int = 10
    ) -> Tuple[List[List[str]], List[List[float]]]:
        """Search for similar vectors.

        Args:
            query_vectors: Query embedding vectors
            k: Number of nearest neighbors

        Returns:
            Tuple of (ids, distances) for each query
        """
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Save index to disk."""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Load index from disk."""
        pass
```

### Creating a New Similarity Backend

#### Step 1: Create Backend Implementation

```python
# nodupe/similarity/backends/my_backend.py
"""My custom similarity backend."""
from typing import List, Tuple
import numpy as np
from .base import SimilarityBackend

class MyBackend(SimilarityBackend):
    """Custom similarity backend using MyIndex.

    This backend uses MyIndex for fast approximate nearest neighbor search.

    Example:
        >>> backend = MyBackend(dim=512)
        >>> backend.add(['file1.jpg'], [embedding1])
        >>> ids, distances = backend.search([query_embedding], k=5)
    """

    def __init__(self, dim: int):
        """Initialize backend.

        Args:
            dim: Embedding dimension
        """
        try:
            import myindex
        except ImportError:
            raise ImportError(
                "MyBackend requires 'myindex'. "
                "Install with: pip install myindex"
            )

        self.dim = dim
        self.index = myindex.Index(dimension=dim)
        self.ids = []  # Track file IDs

    def add(self, ids: List[str], vectors: List[np.ndarray]) -> None:
        """Add vectors to index."""
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors must have same length")

        # Add to index
        for id_, vector in zip(ids, vectors):
            if vector.shape != (self.dim,):
                raise ValueError(f"Expected dim {self.dim}, got {vector.shape}")

            idx = len(self.ids)
            self.index.add_item(idx, vector)
            self.ids.append(id_)

        # Rebuild index for search
        self.index.build()

    def search(
        self,
        query_vectors: List[np.ndarray],
        k: int = 10
    ) -> Tuple[List[List[str]], List[List[float]]]:
        """Search for k nearest neighbors."""
        all_ids = []
        all_distances = []

        for query_vector in query_vectors:
            # Search index
            indices, distances = self.index.search(query_vector, k)

            # Map indices to IDs
            result_ids = [self.ids[idx] for idx in indices]

            all_ids.append(result_ids)
            all_distances.append(distances.tolist())

        return all_ids, all_distances

    def save(self, path: str) -> None:
        """Save index to disk."""
        # Save index structure
        self.index.save(path)

        # Save ID mapping
        import json
        with open(f"{path}.ids", 'w') as f:
            json.dump(self.ids, f)

    def load(self, path: str) -> None:
        """Load index from disk."""
        # Load index structure
        self.index.load(path)

        # Load ID mapping
        import json
        with open(f"{path}.ids", 'r') as f:
            self.ids = json.load(f)
```

#### Step 2: Register Backend

```python
# nodupe/similarity/backends/__init__.py
from typing import Dict, Callable
from .bruteforce_backend import BruteForceBackend
from .faiss_backend import FAISSBackend
from .my_backend import MyBackend  # Import

# Backend factory registry
BACKENDS: Dict[str, Callable] = {
    'bruteforce': lambda dim: BruteForceBackend(dim),
    'faiss': lambda dim: FAISSBackend(dim),
    'my': lambda dim: MyBackend(dim),  # Register
}

def list_backends() -> List[str]:
    """List available backend names."""
    available = []
    for name, factory in BACKENDS.items():
        try:
            # Test if backend can be created
            backend = factory(16)  # Try with small dim
            available.append(name)
        except ImportError:
            pass  # Backend not available
    return available

def get_factory(backend_name: str):
    """Get factory function for backend."""
    if backend_name not in BACKENDS:
        raise ValueError(
            f"Unknown backend '{backend_name}'. "
            f"Available: {list(BACKENDS.keys())}"
        )
    return BACKENDS[backend_name]

def default_backend_name() -> str:
    """Get default/recommended backend name."""
    # Try backends in order of preference
    for name in ['faiss', 'my', 'bruteforce']:
        if name in list_backends():
            return name
    return 'bruteforce'  # Fallback
```

#### Step 3: Use in Index Creation

```python
# nodupe/similarity/index.py
def make_index(dim: int = 16, backend: str = 'auto'):
    """Create similarity index.

    Args:
        dim: Embedding dimension
        backend: Backend name ('auto', 'faiss', 'my', 'bruteforce')

    Returns:
        Index instance with selected backend
    """
    from .backends import get_factory, default_backend_name

    # Auto-select backend
    if backend == 'auto':
        backend = default_backend_name()

    # Get factory and create backend
    factory = get_factory(backend)
    return factory(dim)
```

---

## Backend Selection Logic

### Auto-Selection Strategy

Backends are selected based on:

1. **User preference** (if specified)
2. **Availability** (dependencies installed?)
3. **Performance** (prefer faster backends)

### AI Backend Selection

```python
def choose_backend(preference: Optional[str] = None) -> BaseBackend:
    """Select AI backend with fallback logic."""

    # Priority order (best to worst)
    backends_to_try = [
        ('onnx', ONNXBackend),   # GPU/CPU accelerated
        ('custom', CustomBackend), # User's custom backend
        ('cpu', CPUBackend),      # Pure Python fallback
    ]

    for name, backend_class in backends_to_try:
        # Skip if user wants specific backend
        if preference and preference != name:
            continue

        try:
            backend = backend_class()
            print(f"[AI] Using {name} backend")
            return backend
        except ImportError as e:
            print(f"[AI] {name} unavailable: {e}")
            continue

    raise RuntimeError("No AI backends available")
```

### Similarity Backend Selection

```python
def default_backend_name() -> str:
    """Select best similarity backend."""

    # Try in order of performance
    for backend_name in ['faiss', 'annoy', 'bruteforce']:
        try:
            # Check if backend can be created
            factory = get_factory(backend_name)
            factory(16)  # Test creation
            return backend_name
        except (ImportError, Exception):
            continue

    return 'bruteforce'  # Always available fallback
```

---

## Testing Backends

### Unit Test Template

```python
# tests/test_backends.py
import pytest
import numpy as np
from nodupe.ai.backends.my_backend import MyBackend

class TestMyBackend:
    """Test suite for MyBackend."""

    @pytest.fixture
    def backend(self):
        """Create backend instance."""
        try:
            return MyBackend()
        except ImportError:
            pytest.skip("MyBackend dependencies unavailable")

    def test_initialization(self, backend):
        """Test backend can be initialized."""
        assert backend is not None
        assert backend.get_embedding_dim() > 0

    def test_embedding_shape(self, backend, sample_image):
        """Test embedding has correct shape."""
        embedding = backend.compute_embedding(sample_image)
        expected_dim = backend.get_embedding_dim()

        assert embedding.shape == (expected_dim,)

    def test_embedding_normalized(self, backend, sample_image):
        """Test embeddings are normalized."""
        embedding = backend.compute_embedding(sample_image)
        norm = np.linalg.norm(embedding)

        assert np.isclose(norm, 1.0, atol=1e-5)

    def test_invalid_file(self, backend):
        """Test handling of invalid files."""
        from pathlib import Path
        result = backend.compute_embedding(Path("nonexistent.jpg"))
        assert result is None

    def test_consistency(self, backend, sample_image):
        """Test that same image produces same embedding."""
        emb1 = backend.compute_embedding(sample_image)
        emb2 = backend.compute_embedding(sample_image)

        np.testing.assert_array_almost_equal(emb1, emb2)
```

### Integration Test

```python
def test_backend_integration(tmp_path):
    """Test backend in realistic workflow."""
    from nodupe.ai.backends import choose_backend
    from nodupe.similarity import make_index

    # Get backend
    backend = choose_backend()

    # Create test images
    images = []
    for i in range(10):
        img_path = tmp_path / f"image_{i}.jpg"
        # ... create test image
        images.append(img_path)

    # Compute embeddings
    embeddings = []
    for img_path in images:
        emb = backend.compute_embedding(img_path)
        assert emb is not None
        embeddings.append(emb)

    # Build similarity index
    dim = backend.get_embedding_dim()
    index = make_index(dim=dim, backend='auto')

    # Add to index
    ids = [str(p) for p in images]
    index.add(ids, embeddings)

    # Search
    query_emb = embeddings[0]
    result_ids, distances = index.search([query_emb], k=3)

    # Verify
    assert len(result_ids[0]) == 3
    assert ids[0] in result_ids[0]  # Same image should match
```

---

## Best Practices

### 1. Handle Missing Dependencies Gracefully

```python
# ✅ GOOD: Raise informative error
class MyBackend(BaseBackend):
    def __init__(self):
        try:
            import mypackage
        except ImportError:
            raise ImportError(
                "MyBackend requires 'mypackage'. "
                "Install with: pip install mypackage"
            )

# ❌ BAD: Let import error propagate unchecked
class MyBackend(BaseBackend):
    def __init__(self):
        import mypackage  # May cause cryptic errors
```

### 2. Normalize Embeddings

```python
# ✅ GOOD: Normalize for cosine similarity
def compute_embedding(self, file_path):
    embedding = self.model.encode(image)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding

# ❌ BAD: Unnormalized embeddings
def compute_embedding(self, file_path):
    return self.model.encode(image)  # No normalization
```

### 3. Validate Inputs

```python
# ✅ GOOD: Validate inputs
def add(self, ids, vectors):
    if len(ids) != len(vectors):
        raise ValueError("ids and vectors length mismatch")

    for vector in vectors:
        if vector.shape != (self.dim,):
            raise ValueError(f"Expected dim {self.dim}, got {vector.shape}")

    # ... proceed with adding
```

### 4. Handle Errors Gracefully

```python
# ✅ GOOD: Return None on error (don't crash)
def compute_embedding(self, file_path):
    try:
        return self._compute(file_path)
    except Exception as e:
        print(f"[Backend] Error: {e}")
        return None  # Allows processing to continue

# ❌ BAD: Let exceptions crash application
def compute_embedding(self, file_path):
    return self._compute(file_path)  # May raise
```

### 5. Document Performance Characteristics

```python
class MyBackend(BaseBackend):
    """Custom AI backend.

    Performance:
        - Compute time: ~50ms per image (GPU)
        - Memory: ~2GB for model
        - Accuracy: 92% on ImageNet

    Requirements:
        - GPU: Optional but recommended
        - VRAM: 2GB minimum
        - Dependencies: mypackage>=1.0
    """
```

---

## Examples

### Example 1: Lightweight CPU Backend

```python
# nodupe/ai/backends/simple_backend.py
"""Simple CPU-based backend using basic features."""
import numpy as np
from pathlib import Path
from typing import Optional
from PIL import Image
from .base import BaseBackend

class SimpleBackend(BaseBackend):
    """Simple backend using color histograms.

    This is a lightweight backend that doesn't require ML models.
    It uses color histograms for basic similarity detection.

    Good for: Fast prototyping, limited resources
    Not good for: Semantic similarity, complex scenes
    """

    def __init__(self, bins: int = 32):
        """Initialize simple backend.

        Args:
            bins: Number of histogram bins per channel
        """
        self.bins = bins
        self.dim = bins * 3  # RGB channels

    def compute_embedding(self, file_path: Path) -> Optional[np.ndarray]:
        """Compute color histogram embedding."""
        try:
            # Load image
            img = Image.open(file_path).convert('RGB')

            # Resize for consistency
            img = img.resize((256, 256))

            # Compute histograms per channel
            histograms = []
            for channel in range(3):  # RGB
                channel_data = np.array(img)[:, :, channel]
                hist, _ = np.histogram(
                    channel_data,
                    bins=self.bins,
                    range=(0, 256)
                )
                histograms.append(hist)

            # Concatenate and normalize
            embedding = np.concatenate(histograms).astype(float)
            embedding /= np.linalg.norm(embedding)

            return embedding

        except Exception as e:
            print(f"[SimpleBackend] Error: {e}")
            return None

    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.dim
```

### Example 2: GPU-Accelerated Backend

```python
# nodupe/ai/backends/gpu_backend.py
"""GPU-accelerated backend using CUDA."""
import numpy as np
from pathlib import Path
from typing import Optional
import torch
from .base import BaseBackend

class GPUBackend(BaseBackend):
    """GPU-accelerated backend using PyTorch.

    Requires:
        - PyTorch with CUDA support
        - GPU with 4GB+ VRAM
    """

    def __init__(self, model_name: str = 'resnet50'):
        """Initialize GPU backend.

        Args:
            model_name: Model architecture to use
        """
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA not available")

        import torchvision.models as models

        # Load model
        self.device = torch.device('cuda')
        self.model = getattr(models, model_name)(pretrained=True)
        self.model = self.model.to(self.device)
        self.model.eval()

        # Remove classification head (keep features only)
        self.model = torch.nn.Sequential(
            *list(self.model.children())[:-1]
        )

        self.dim = 2048  # ResNet50 feature dimension

    def compute_embedding(self, file_path: Path) -> Optional[np.ndarray]:
        """Compute embedding using GPU."""
        try:
            from torchvision import transforms
            from PIL import Image

            # Load and preprocess
            img = Image.open(file_path).convert('RGB')
            transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])
            img_tensor = transform(img).unsqueeze(0).to(self.device)

            # Compute embedding
            with torch.no_grad():
                embedding = self.model(img_tensor)

            # Convert to numpy and normalize
            embedding = embedding.cpu().numpy().flatten()
            embedding /= np.linalg.norm(embedding)

            return embedding

        except Exception as e:
            print(f"[GPUBackend] Error: {e}")
            return None

    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.dim
```

---

## Summary

**To add a new backend:**

1. ✅ Inherit from `BaseBackend` (AI) or `SimilarityBackend`
2. ✅ Implement required methods
3. ✅ Add to backend selection logic
4. ✅ Write tests
5. ✅ Document dependencies and performance

**Key Principles:**

- **Abstract Interface** - Follow base class contract
- **Graceful Degradation** - Handle missing dependencies
- **Error Handling** - Return None instead of crashing
- **Normalization** - Normalize embeddings for consistency
- **Testing** - Verify correctness and performance

**See Also:**

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DEPENDENCY_INJECTION.md](DEPENDENCY_INJECTION.md) - DI patterns
- [ADDING_COMMANDS.md](ADDING_COMMANDS.md) - Command development

---

**Document Version:** 1.0
**Maintainer:** NoDupeLabs Team
**License:** Apache-2.0
