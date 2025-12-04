# Similarity / Embedding Plugin System

NoDupeLabs now supports a pluggable similarity backend architecture. Backends live under `nodupe/similarity/backends/` and are dynamically discovered at runtime.

Core concepts
- Each backend module must expose a `create(dim: int)` factory that returns an object implementing `add(vectors, ids)` and `search(vector, k)`.
- Optionally, backend modules may expose `available()` to indicate runtime availability (e.g. whether required dependencies are present).

Provided backends
- `bruteforce_backend.py` — pure-Python, always available. Uses NumPy for a simple in-memory brute-force index.
- `faiss_backend.py` — GPU/CPU-accelerated FAISS backend when `faiss` is installed.

Using the system
- Build an index from the DB:
  ```bash
  nodupe similarity build --dim 16
  ```

- Query the in-memory index for near-duplicates of a file:
  ```bash
  nodupe similarity query /path/to/image.jpg --dim 16 -k 5
  ```

Adding a new backend
1.  Place a new Python module under `nodupe/similarity/backends/` (e.g. `my_backend.py`).
2.  Implement a `create(dim: int)` function returning an index object with `add()` and `search()`.
3.  (Optional) Add an `available()` function so the loader can prefer available backends.

Because backends are discovered dynamically, you can add or remove them without changing the rest of the codebase.
