# NoDupeLabs Similarity Search System

This guide provides comprehensive documentation for the pluggable similarity backend architecture in NoDupeLabs.

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Provided Backends](#provided-backends)
- [Usage Examples](#usage-examples)
- [Adding New Backends](#adding-new-backends)
- [Advanced Usage](#advanced-usage)

## Overview

NoDupeLabs supports a pluggable similarity backend architecture for finding near-duplicate files using vector embeddings. Backends are dynamically discovered at runtime and can be extended without modifying the core codebase.

## Core Concepts

### Backend Interface

Each similarity backend must implement:

- **`create(dim: int)`**: Factory function returning an index object
- **`add(vectors, ids)`**: Add vectors to the index
- **`search(vector, k)`**: Search for nearest neighbors
- **`available()`** (optional): Check runtime availability

### Dynamic Discovery

- Backends are automatically discovered in `nodupe/similarity/backends/`
- No code changes required to add/remove backends
- Runtime availability checking for dependencies

## Provided Backends

### Brute-Force Backend

```bash
# Pure-Python backend using NumPy
# Always available, no additional dependencies
# Suitable for small to medium datasets

nodupe similarity build --backend bruteforce --dim 16
```

**Features**:
- Always available (requires only NumPy)
- Simple in-memory brute-force index
- Exact nearest neighbor search (L2 distance)
- Suitable for datasets up to ~10,000 items

### FAISS Backend

```bash
# GPU/CPU-accelerated backend using Facebook AI Similarity Search
# Requires faiss-cpu or faiss-gpu package
# Suitable for large datasets with hardware acceleration

nodupe similarity build --backend faiss --dim 16
```

**Features**:
- Hardware acceleration (GPU/CPU)
- Approximate nearest neighbor search
- Scalable to millions of items
- Requires `faiss` package installation

## Usage Examples

### Building Similarity Indexes

```bash
# Build index with brute-force backend
nodupe similarity build --out index.npz --dim 16 --backend bruteforce

# Build index with FAISS backend (if available)
nodupe similarity build --out index.faiss --dim 32 --backend faiss

# Build index with custom dimension
nodupe similarity build --out index_64.npz --dim 64
```

### Querying for Similar Files

```bash
# Query with brute-force index
nodupe similarity query photo.jpg --index-file index.npz -k 10

# Query with FAISS index
nodupe similarity query photo.jpg --index-file index.faiss -k 5

# Query with different number of results
nodupe similarity query photo.jpg --index-file index.npz -k 20
```

### Index Management

```bash
# Update existing index with new files
nodupe scan --root /new_files
nodupe similarity update --index-file index.npz

# Rebuild index completely
nodupe similarity update --index-file index.npz --rebuild

# List available backends
nodupe similarity list-backends
```

## Adding New Backends

### Step-by-Step Guide

1. **Create backend module**:
   ```bash
   # Place in nodupe/similarity/backends/
   touch nodupe/similarity/backends/my_backend.py
   ```

2. **Implement required functions**:
   ```python
   # my_backend.py
   def create(dim: int):
       """Create and return index object."""
       return MyIndex(dim)

   def available() -> bool:
       """Check if backend is available."""
       return True

   class MyIndex:
       def add(self, vectors, ids=None):
           """Add vectors to index."""
           pass

       def search(self, vector, k=5):
           """Search for nearest neighbors."""
           pass
   ```

3. **Test the backend**:
   ```bash
   # Test with new backend
   nodupe similarity build --backend my_backend --dim 16
   nodupe similarity query test.jpg --index-file index.npz
   ```

### Backend Development Best Practices

- **Error handling**: Graceful degradation if dependencies missing
- **Performance**: Optimize for your target use case
- **Documentation**: Complete docstrings and examples
- **Testing**: Unit tests for backend functionality

## Advanced Usage

### Multiple Indexes for Different Use Cases

```bash
# Create indexes with different dimensions
nodupe similarity build --out index_16.npz --dim 16
nodupe similarity build --out index_32.npz --dim 32
nodupe similarity build --out index_64.npz --dim 64

# Query with appropriate index
nodupe similarity query photo.jpg --index-file index_16.npz -k 10
nodupe similarity query photo.jpg --index-file index_64.npz -k 5
```

### Index Persistence Formats

```bash
# Save in different formats
nodupe similarity build --out index.npz --dim 16  # NumPy compressed
nodupe similarity build --out index.json --dim 16 # JSON format
nodupe similarity build --out index.jsonl --dim 16 # JSON Lines

# Load from different formats
nodupe similarity query photo.jpg --index-file index.npz
nodupe similarity query photo.jpg --index-file index.json
```

### Performance Optimization

```bash
# Optimize for large datasets
nodupe similarity build --backend faiss --dim 64 --gpu

# Optimize for accuracy
nodupe similarity build --backend bruteforce --dim 128

# Optimize for speed
nodupe similarity build --backend faiss --dim 32 --approximate
```

## Troubleshooting

### Common Issues

**Issue**: Backend not available

```bash
# Check available backends
nodupe similarity list-backends

# Install missing dependencies
pip install faiss-cpu  # For FAISS backend
pip install numpy     # For brute-force backend
```

**Issue**: Index file not found

```bash
# Verify index file exists
ls -la index.npz

# Rebuild if missing
nodupe similarity build --out index.npz --dim 16
```

**Issue**: Query returns no results

```bash
# Check index contains data
nodupe similarity info --index-file index.npz

# Ensure correct dimension
nodupe similarity query photo.jpg --index-file index.npz --dim 16
```

## Best Practices

### Index Dimension Selection

| Use Case | Recommended Dimension |
|----------|----------------------|
| Thumbnails | 16-32 |
| Small images | 32-64 |
| High-res images | 64-128 |
| Videos (frames) | 128-256 |

### Backend Selection Guide

| Backend | Use Case | Requirements |
|---------|----------|--------------|
| Brute-force | Small datasets, always available | NumPy |
| FAISS | Large datasets, performance | faiss-cpu/gpu |
| Custom | Specialized needs | Your dependencies |

## Conclusion

The NoDupeLabs similarity search system provides a **flexible, extensible architecture** for finding near-duplicate files. Use the provided backends or create your own to suit your specific needs.

**Next Steps**:
- Try the [Advanced Usage Guide](ADVANCED_USAGE.md) for complex scenarios
- Explore [Integration Guides](INTEGRATION_GUIDES.md) for platform examples
- Review [Documentation Guide](DOCUMENTATION_GUIDE.md) to contribute new backends
