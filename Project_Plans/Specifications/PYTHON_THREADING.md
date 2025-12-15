# Python Threading Support Specification

## Overview

This document describes Python's modern threading capabilities and parallelism mechanisms as of Python 3.13 (2024) and Python 3.14 (2025), including the revolutionary free-threaded mode and per-interpreter GIL improvements.

**Last Updated**: December 2025
**Python Versions Covered**: 3.12, 3.13, 3.14

---

## Major Threading Evolution Timeline

### Python 3.12 (October 2023)
- **PEP 684**: Per-Interpreter GIL
- Each subinterpreter gets its own GIL
- True parallel execution across subinterpreters
- Foundation for future free-threading

### Python 3.13 (October 2024)
- **PEP 703**: Experimental Free-Threaded Mode (GIL Optional)
- **PEP 744**: JIT Compiler
- Build flag: `--disable-gil`
- Experimental binaries: `python3.13t`
- ~40% performance overhead on single-threaded code

### Python 3.14 (October 2025) - Current Stable
- **Free-Threading Reaches Supported Status** (PEP 779)
- **PEP 734**: Multiple Interpreters in Standard Library
- **Performance Improvement**: 5-10% overhead (down from 40%)
- Adaptive interpreter re-enabled in free-threaded mode
- `concurrent.futures.InterpreterPoolExecutor` added
- Free-threading no longer experimental

---

## 1. Free-Threaded Mode (PEP 703)

### What is Free-Threading?

Free-threaded Python allows running Python code without the Global Interpreter Lock (GIL), enabling true parallel execution of Python threads on multiple CPU cores.

### Key Features

**Python 3.13** (Experimental):
- Disabled by default
- Requires special build: `--disable-gil`
- Special executables: `python3.13t` or `python3.13t.exe`
- ~40% single-threaded overhead
- Available in official Windows and macOS installers

**Python 3.14** (Supported):
- Officially supported (PEP 779 criteria met)
- 5-10% single-threaded overhead (major improvement)
- Specializing adaptive interpreter (PEP 659) enabled
- C API changes finalized
- Production-ready for multi-threaded workloads

### Building Free-Threaded Python

```bash
# From source
./configure --disable-gil
make
make install

# Using official installers (3.13+)
# Windows: python3.13t.exe
# macOS: python3.13t
```

### Performance Characteristics

| Metric | Python 3.13 (Experimental) | Python 3.14 (Supported) |
|--------|---------------------------|------------------------|
| Single-threaded overhead | ~40% | 5-10% |
| Multi-threaded speedup | Linear with cores | Linear with cores |
| Adaptive interpreter | Disabled | Enabled |
| Production ready | No | Yes |

### When to Use Free-Threading

**Best For**:
- CPU-intensive parallel workloads
- Multi-core utilization
- Thread-based concurrent algorithms
- Scientific computing with threads
- Parallel data processing

**Not Ideal For**:
- I/O-bound tasks (use asyncio instead)
- Single-threaded applications
- Libraries not yet thread-safe

### Code Example

```python
import threading
import sys

def cpu_intensive_work(n):
    """CPU-bound calculation"""
    result = 0
    for i in range(n):
        result += i ** 2
    return result

# Check if running in free-threaded mode
if sys.flags.gil == 0:
    print("Running in free-threaded mode!")

    # This will actually run in parallel on multiple cores
    threads = []
    for i in range(4):
        t = threading.Thread(target=cpu_intensive_work, args=(10_000_000,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
else:
    print("Running with GIL enabled")
```

---

## 2. Per-Interpreter GIL (PEP 684)

### Overview

Introduced in Python 3.12, each subinterpreter has its own GIL, allowing true parallel execution across interpreters while maintaining isolation.

### Key Benefits

1. **True Parallelism**: Different interpreters can run Python code simultaneously
2. **Isolation**: Each interpreter has its own namespace and state
3. **Efficiency**: More efficient than multiprocessing (shared process resources)
4. **Safety**: No shared Python objects between interpreters

### Architecture

```
Process
├── Main Interpreter (GIL 1)
├── Subinterpreter 1 (GIL 2)
├── Subinterpreter 2 (GIL 3)
└── Subinterpreter 3 (GIL 4)
```

Each interpreter can execute Python code in parallel with others.

### Comparison: Interpreters vs Multiprocessing vs Threading

| Feature | Subinterpreters | Multiprocessing | Threading (with GIL) |
|---------|----------------|-----------------|---------------------|
| Parallelism | ✅ True | ✅ True | ❌ Concurrent only |
| Memory overhead | 🟢 Low | 🔴 High | 🟢 Lowest |
| Startup time | 🟢 Fast | 🔴 Slow | 🟢 Fastest |
| Isolation | ✅ Strong | ✅ Complete | ❌ Shared memory |
| Communication | Queue-based | IPC/Pipes | Direct |
| CPU-bound tasks | ✅ Excellent | ✅ Excellent | ❌ Poor |
| I/O-bound tasks | ✅ Good | ✅ Good | ✅ Excellent |

---

## 3. Multiple Interpreters Module (PEP 734)

### Overview

Python 3.14 adds the `interpreters` module to the standard library, providing a high-level interface for working with multiple interpreters.

### Key Components

#### `interpreters` Module

```python
import interpreters

# Create a new interpreter
interp = interpreters.create()

# Run code in the interpreter
interp.exec("""
import math
result = math.sqrt(16)
print(f"Result: {result}")
""")

# Close interpreter
interp.close()
```

#### `InterpreterPoolExecutor`

```python
from concurrent.futures import InterpreterPoolExecutor

def compute(x):
    return x ** 2

# Similar to ThreadPoolExecutor/ProcessPoolExecutor
with InterpreterPoolExecutor(max_interpreters=4) as executor:
    results = executor.map(compute, range(100))
    print(list(results))
```

### Communication Between Interpreters

#### Built-in Queue

```python
import interpreters

# Create a queue for communication
queue = interpreters.Queue()

# Interpreter 1: Producer
interp1 = interpreters.create()
interp1.exec(f"""
import interpreters
queue = interpreters.Queue.from_id({queue.id})
queue.put("Hello from interpreter 1!")
""")

# Interpreter 2: Consumer
interp2 = interpreters.create()
interp2.exec(f"""
import interpreters
queue = interpreters.Queue.from_id({queue.id})
message = queue.get()
print(f"Received: {{message}}")
""")
```

### Use Cases for Subinterpreters

1. **Plugin Systems**: Isolate untrusted code
2. **Parallel Data Processing**: Process large datasets in parallel
3. **Web Servers**: Handle requests in isolated interpreters
4. **Scientific Computing**: Parallel simulations with isolation
5. **Testing**: Run tests in isolation without subprocess overhead

---

## 4. Concurrent Execution Patterns

### Standard Library Options

#### 1. `threading` - Traditional Threading

```python
import threading

def worker(name):
    print(f"Worker {name} running")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

**Best For**: I/O-bound tasks with GIL, simple concurrency

#### 2. `concurrent.futures.ThreadPoolExecutor`

```python
from concurrent.futures import ThreadPoolExecutor

def process_item(item):
    return item * 2

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(process_item, range(100))
```

**Best For**: I/O-bound tasks, simple parallel mapping

#### 3. `concurrent.futures.ProcessPoolExecutor`

```python
from concurrent.futures import ProcessPoolExecutor

def cpu_intensive(n):
    return sum(i*i for i in range(n))

with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(cpu_intensive, [10**7] * 4)
```

**Best For**: CPU-bound tasks (traditional approach with GIL)

#### 4. `concurrent.futures.InterpreterPoolExecutor` (NEW in 3.14)

```python
from concurrent.futures import InterpreterPoolExecutor

def parallel_task(data):
    # Runs in isolated interpreter
    return process_data(data)

with InterpreterPoolExecutor(max_interpreters=4) as executor:
    results = executor.map(parallel_task, dataset)
```

**Best For**: CPU-bound tasks with better efficiency than processes

#### 5. `asyncio` - Asynchronous I/O

```python
import asyncio

async def async_task(name):
    await asyncio.sleep(1)
    return f"Task {name} complete"

async def main():
    tasks = [async_task(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

asyncio.run(main())
```

**Best For**: I/O-bound tasks, network operations, high concurrency

---

## 5. Decision Matrix: Choosing the Right Tool

### Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│                    CONCURRENCY DECISION TREE                 │
└─────────────────────────────────────────────────────────────┘

Is the task CPU-bound or I/O-bound?
│
├─ CPU-BOUND (computation-heavy)
│  │
│  ├─ Python 3.14+ with free-threading?
│  │  └─ YES → threading.Thread (free-threaded mode)
│  │
│  ├─ Need isolation between tasks?
│  │  └─ YES → InterpreterPoolExecutor (3.14+)
│  │          or ProcessPoolExecutor (3.12+)
│  │
│  └─ Maximum compatibility?
│     └─ ProcessPoolExecutor (works everywhere)
│
└─ I/O-BOUND (network, disk, database)
   │
   ├─ Using async libraries?
   │  └─ YES → asyncio (best performance)
   │
   ├─ Simple threading needs?
   │  └─ ThreadPoolExecutor or threading.Thread
   │
   └─ Need isolation?
      └─ InterpreterPoolExecutor (3.14+)
```

### Detailed Comparison

| Pattern | CPU-Bound | I/O-Bound | Isolation | Memory | Startup | GIL Impact |
|---------|-----------|-----------|-----------|--------|---------|------------|
| **threading** (with GIL) | ❌ | ✅ | ❌ | 🟢 Low | 🟢 Fast | 🔴 Limited |
| **threading** (free-threaded) | ✅ | ✅ | ❌ | 🟢 Low | 🟢 Fast | 🟢 None |
| **ThreadPoolExecutor** | ❌* | ✅ | ❌ | 🟢 Low | 🟢 Fast | 🔴 Limited |
| **ProcessPoolExecutor** | ✅ | ✅ | ✅ | 🔴 High | 🔴 Slow | 🟢 None |
| **InterpreterPoolExecutor** | ✅ | ✅ | ✅ | 🟡 Medium | 🟢 Fast | 🟢 None |
| **asyncio** | ❌ | ✅✅ | ❌ | 🟢 Low | 🟢 Fast | N/A |

*✅ if using free-threaded Python 3.13+

---

## 6. Thread Safety Considerations

### Free-Threaded Mode Requirements

When using free-threaded Python, ensure:

1. **Use Thread-Safe Data Structures**:
   ```python
   import threading
   from queue import Queue

   # Thread-safe queue
   work_queue = Queue()

   # Thread-safe counter
   counter = 0
   counter_lock = threading.Lock()

   def increment():
       global counter
       with counter_lock:
           counter += 1
   ```

2. **Protect Shared State**:
   ```python
   import threading

   class ThreadSafeCache:
       def __init__(self):
           self._cache = {}
           self._lock = threading.RLock()

       def get(self, key):
           with self._lock:
               return self._cache.get(key)

       def set(self, key, value):
           with self._lock:
               self._cache[key] = value
   ```

3. **Use Atomic Operations**:
   ```python
   from threading import Lock

   class AtomicCounter:
       def __init__(self):
           self._value = 0
           self._lock = Lock()

       def increment(self):
           with self._lock:
               self._value += 1
               return self._value
   ```

### Library Compatibility

**Free-Threading Compatible** (as of 2025):
- ✅ Most standard library modules
- ✅ NumPy (1.26+)
- ✅ SciPy
- ✅ Pillow
- ✅ Requests
- ✅ SQLAlchemy

**Needs Updates**:
- ⚠️ Some C extensions
- ⚠️ Libraries with global state
- ⚠️ Legacy code assuming GIL protection

---

## 7. Best Practices

### General Threading

1. **Minimize Shared State**: Use message passing over shared memory
2. **Use Context Managers**: Ensure proper resource cleanup
3. **Avoid Deadlocks**: Acquire locks in consistent order
4. **Set Daemon Threads Carefully**: Understand lifecycle implications
5. **Use Thread Pools**: Avoid creating too many threads

### Free-Threaded Python

1. **Profile First**: Measure if free-threading helps your workload
2. **Start Conservative**: Begin with low thread counts
3. **Test Thoroughly**: Concurrent bugs are harder to reproduce
4. **Update Dependencies**: Ensure libraries are free-threading compatible
5. **Monitor Performance**: 5-10% overhead acceptable for parallelism gains

### NoDupeLabs Specific Best Practices

#### GIL Detection and Adaptation
- **Always detect GIL status** at runtime using `sys.flags.gil`
- **Use RLock instead of Lock** when possible for better re-entrancy
- **Adjust worker counts** based on free-threaded status (2x in free-threaded mode)
- **Prefer InterpreterPoolExecutor** for CPU-bound tasks in Python 3.14+

#### Code Examples for GIL-Aware Programming

**Example 1: Adaptive Worker Count**
```python
import sys
from multiprocessing import cpu_count

def get_optimal_workers(task_type='cpu'):
    cpu_cores = cpu_count()

    if hasattr(sys, 'flags') and getattr(sys.flags, 'gil', 1) == 0:
        # Free-threaded Python - can use more workers
        if task_type == 'cpu':
            return cpu_cores * 2
        else:
            return min(32, cpu_cores * 2)
    else:
        # Traditional GIL mode - be conservative
        if task_type == 'cpu':
            return min(32, cpu_cores)
        else:
            return min(32, cpu_cores * 2)
```

**Example 2: Smart Executor Selection**
```python
def smart_executor(func, items, task_type='cpu'):
    import sys

    major, minor = sys.version_info.major, sys.version_info.minor

    if task_type == 'cpu':
        if major >= 3 and minor >= 14:
            # Use InterpreterPoolExecutor for Python 3.14+
            from concurrent.futures import InterpreterPoolExecutor
            with InterpreterPoolExecutor() as executor:
                return list(executor.map(func, items))
        elif hasattr(sys, 'flags') and getattr(sys.flags, 'gil', 1) == 0:
            # Free-threaded Python - use threads
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor() as executor:
                return list(executor.map(func, items))
        else:
            # Traditional Python - use processes
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor() as executor:
                return list(executor.map(func, items))
    else:  # I/O-bound
        # Always use threads for I/O
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            return list(executor.map(func, items))
```

**Example 3: Free-Threaded Compatible Pool Creation**
```python
from nodupe.core.pools import Pools

# Use optimized pool creation that adapts to Python version
pool = Pools.create_pool_optimized(
    factory=lambda: create_database_connection(),
    max_size=10
)

# Or for worker pools
worker_pool = Pools.create_worker_pool_optimized(
    workers=4,
    queue_size=100
)
```

#### Thread Safety in Free-Threading Mode
- **Always use proper synchronization** - don't assume GIL protection
- **Test with both GIL and free-threaded modes** during development
- **Use atomic operations** for simple counters and flags
- **Prefer immutable data structures** when possible
- **Implement proper cleanup** in context managers

#### Performance Optimization Strategies
- **For CPU-bound tasks**:
  - Python 3.14+ → InterpreterPoolExecutor
  - Free-threaded Python 3.13 → ThreadPoolExecutor
  - Traditional Python → ProcessPoolExecutor
- **For I/O-bound tasks**: Always use ThreadPoolExecutor
- **For mixed workloads**: Use smart selection based on Python version and task type
- **Pool sizing**: Double sizes in free-threaded mode for better resource utilization

#### Worker Pool Optimizations
- **Use optimized factory methods** - Use `Pools.create_worker_pool_optimized()` for automatic worker count scaling
- **Check free-threaded status** - Worker pools automatically double worker counts in free-threaded mode
- **Use RLock for better re-entrancy** - All pools now use RLock for improved free-threaded compatibility
- **Adaptive worker counts** - `get_optimal_workers()` returns 2x workers in free-threaded mode

#### Error Handling Considerations
- **Concurrent exceptions** require more robust error handling
- **Resource cleanup** must be thread-safe and atomic
- **Timeout handling** should account for different execution models
- **Logging** should include thread/interpreter context for debugging

#### Complete Usage Example
**Optimized Parallel Processing Pipeline:**
```python
from nodupe.core.parallel import Parallel, parallel_map
from nodupe.core.pools import Pools

def process_large_dataset(data_chunks):
    """Process data chunks in parallel with automatic optimization."""

    # Automatic executor selection based on Python version
    if Parallel.is_free_threaded():
        print(f"Free-threaded Python detected - using {Parallel.get_optimal_workers('cpu')} workers")
        results = Parallel.smart_map(
            func=process_chunk,
            items=data_chunks,
            task_type='cpu',
            workers=Parallel.get_optimal_workers('cpu')
        )
    elif Parallel.supports_interpreter_pool():
        print("Python 3.14+ detected - using InterpreterPoolExecutor")
        results = Parallel.map_parallel(
            func=process_chunk,
            items=data_chunks,
            use_interpreters=True,
            workers=Parallel.get_optimal_workers('cpu')
        )
    else:
        print("Traditional Python - using ProcessPoolExecutor")
        results = Parallel.map_parallel(
            func=process_chunk,
            items=data_chunks,
            use_processes=True,
            workers=Parallel.get_optimal_workers('cpu')
        )

    return results

def setup_optimized_pools():
    """Create optimized pools based on Python version."""

    # Optimized object pool
    obj_pool = Pools.create_pool_optimized(
        factory=lambda: create_processing_object(),
        max_size=20
    )

    # Optimized connection pool (2x connections in free-threaded mode)
    conn_pool = Pools.create_connection_pool_optimized(
        connect_func=lambda: create_db_connection(),
        max_connections=10
    )

    # Optimized worker pool (2x workers in free-threaded mode)
    worker_pool = Pools.create_worker_pool_optimized(
        workers=4,
        queue_size=200
    )

    return obj_pool, conn_pool, worker_pool

# Example usage
if __name__ == "__main__":
    # Set up optimized infrastructure
    obj_pool, conn_pool, worker_pool = setup_optimized_pools()

    # Process data with automatic optimization
    data = load_large_dataset()
    results = process_large_dataset(data)
```

These best practices ensure your NoDupeLabs code remains compatible across different Python versions while taking advantage of the latest threading innovations.

### Subinterpreters

1. **Isolate Untrusted Code**: Great for plugin systems
2. **Use InterpreterPoolExecutor**: Easier than manual management
3. **Minimize Communication**: Keep interpreters independent
4. **Clean Up Resources**: Always close interpreters when done

### AsyncIO

1. **Use for I/O**: Best for network/disk operations
2. **Avoid CPU-Bound Work**: Don't block the event loop
3. **Combine with Threading**: Use `run_in_executor()` for blocking calls
4. **Handle Exceptions**: Uncaught exceptions stop tasks

---

## 8. NoDupeLabs Implementation Recommendations

Based on our parallel processing modules (`parallel.py`, `pools.py`), here are the current implementations and recommendations:

### Current Implementation Status

Our current implementation now includes:
- ✅ `ThreadPoolExecutor` for I/O-bound tasks
- ✅ `ProcessPoolExecutor` for CPU-bound tasks
- ✅ `InterpreterPoolExecutor` for Python 3.14+ CPU-bound tasks
- ✅ Thread-safe pools and queues with RLock optimization
- ✅ Proper resource cleanup with context managers
- ✅ Smart executor selection with `smart_map()`
- ✅ Free-threaded Python detection and adaptation
- ✅ Optimized factory methods in `Pools` class

### Pool Optimization Features

**Object Pool Optimizations:**
- ✅ `is_free_threaded` property for runtime detection
- ✅ `get_optimal_pool_size()` method for adaptive sizing
- ✅ RLock usage for better re-entrancy in free-threaded mode
- ✅ `create_pool_optimized()` factory method with adaptive sizing

**Connection Pool Optimizations:**
- ✅ `is_free_threaded` property for runtime detection
- ✅ `create_connection_pool_optimized()` factory method with 2x connection capacity in free-threaded mode

**Worker Pool Optimizations:**
- ✅ `is_free_threaded` property for runtime detection
- ✅ `get_optimal_workers()` method for adaptive worker counts
- ✅ RLock usage for better free-threaded compatibility
- ✅ `create_worker_pool_optimized()` factory method with adaptive worker counts

### Pool-Related Code Examples

**Example 1: Optimized Pool Creation**
```python
from nodupe.core.pools import Pools

# Use optimized factory methods that adapt to Python version
object_pool = Pools.create_pool_optimized(
    factory=lambda: create_cache_object(),
    max_size=10
)

connection_pool = Pools.create_connection_pool_optimized(
    connect_func=lambda: create_database_connection(),
    max_connections=10
)

worker_pool = Pools.create_worker_pool_optimized(
    workers=4,
    queue_size=100
)

# Check if running in free-threaded mode
if worker_pool.is_free_threaded:
    print(f"Worker pool optimized for free-threaded Python with {worker_pool.get_optimal_workers()} workers")
```

**Example 2: Pool Size Adaptation**
```python
from nodupe.core.pools import ObjectPool

# Create pool with adaptive sizing
pool = ObjectPool(
    factory=lambda: create_resource(),
    max_size=10
)

# Get optimal size based on expected concurrent usage
optimal_size = pool.get_optimal_pool_size(estimated_concurrent_usage=8)
print(f"Optimal pool size for current Python version: {optimal_size}")
```

**Example 3: Runtime Pool Optimization**
```python
from nodupe.core.pools import Pools

# Check the current threading model
if Pools.is_free_threaded():
    print("Running in free-threaded mode - pools will use enhanced threading")
    # Pools automatically use more aggressive optimization strategies
else:
    print("Running with GIL - using traditional threading strategies")

# Create appropriately sized pools
pool = Pools.create_pool_optimized(
    factory=lambda: create_worker_object(),
    max_size=5  # Will be doubled to 10 in free-threaded mode
)
```

### Recommended Enhancements

#### 1. NoDupeLabs Implementation Status

The NoDupeLabs parallel processing modules have been updated with comprehensive support for modern Python threading:

**Free-Threading Detection and Optimization:**
- ✅ `Parallel.is_free_threaded()` - Detects free-threaded mode at runtime
- ✅ `Parallel.get_python_version_info()` - Gets current Python version
- ✅ `Parallel.supports_interpreter_pool()` - Checks for InterpreterPoolExecutor support
- ✅ `Parallel.get_optimal_workers()` - Returns optimized worker counts based on Python version

**Interpreter Pool Executor Support:**
- ✅ `use_interpreters` parameter added to `process_in_parallel()`, `map_parallel()`, `map_parallel_unordered()`, `process_batches()`, and `reduce_parallel()` methods
- ✅ Automatic selection via `smart_map()` function that intelligently chooses the best executor

**Updated Code Examples:**

**Example 1: Basic Interpreter Pool Usage**
```python
from nodupe.core.parallel import Parallel

# Explicit interpreter usage (Python 3.14+)
results = Parallel.map_parallel(
    func=cpu_intensive_task,
    items=data,
    use_interpreters=True,
    workers=4
)

# Smart execution that automatically chooses best executor
results = Parallel.smart_map(
    func=cpu_intensive_task,
    items=data,
    task_type='cpu',  # or 'io' for I/O-bound tasks
    workers=4
)
```

**Example 2: Updated Convenience Functions**
```python
from nodupe.core.parallel import parallel_map, parallel_filter, parallel_starmap

# All convenience functions now support interpreter pools
results = parallel_map(
    func=process_item,
    items=data,
    use_processes=False,
    use_interpreters=True  # Python 3.14+ only
)

filtered = parallel_filter(
    predicate=is_duplicate,
    items=files,
    use_interpreters=True
)

results = parallel_starmap(
    func=process_file_with_params,
    args_list=param_tuples,
    use_interpreters=True
)

**Example 3: Complete Interpreter Pool Usage Pattern**
```python
from nodupe.core.parallel import Parallel

# Detect Python capabilities
if Parallel.supports_interpreter_pool():
    print("Using InterpreterPoolExecutor for maximum efficiency")
    results = Parallel.map_parallel(
        func=cpu_intensive_hash_calculation,
        items=large_file_list,
        use_interpreters=True,
        workers=Parallel.get_optimal_workers('cpu')
    )
elif Parallel.is_free_threaded():
    print("Using ThreadPoolExecutor in free-threaded mode")
    results = Parallel.map_parallel(
        func=cpu_intensive_hash_calculation,
        items=large_file_list,
        use_processes=False,
        workers=Parallel.get_optimal_workers('cpu')
    )
else:
    print("Using ProcessPoolExecutor with GIL")
    results = Parallel.map_parallel(
        func=cpu_intensive_hash_calculation,
        items=large_file_list,
        use_processes=True,
        workers=Parallel.get_optimal_workers('cpu')
    )

# Or use the smart_map for automatic selection
results = Parallel.smart_map(
    func=cpu_intensive_hash_calculation,
    items=large_file_list,
    task_type='cpu'
)
```

### Parallel Processing API

The NoDupeLabs project includes a comprehensive `Parallel` class that provides intelligent executor selection based on Python version and threading capabilities:

#### Core Detection Methods

```python
from nodupe.core.parallel import Parallel

# Check if running in free-threaded mode
if Parallel.is_free_threaded():
    print("Running in free-threaded mode")

# Get Python version information
major, minor = Parallel.get_python_version_info()

# Check if InterpreterPoolExecutor is available (Python 3.14+)
supports_interpreters = Parallel.supports_interpreter_pool()
```

#### Core Processing Methods

**Process in Parallel:**
```python
# Basic usage
results = Parallel.process_in_parallel(
    func=worker_function,
    items=data_list,
    workers=4,
    use_processes=False,  # Use threads
    use_interpreters=True  # Python 3.14+ only
)

# With timeout
results = Parallel.process_in_parallel(
    func=worker_function,
    items=data_list,
    timeout=30.0
)
```

**Map Operations:**
```python
# Parallel mapping with interpreter support
results = Parallel.map_parallel(
    func=processor,
    items=data,
    workers=6,
    use_processes=False,
    use_interpreters=True  # Use interpreters when available
)

# Unordered mapping (returns results as they complete)
for result in Parallel.map_parallel_unordered(
    func=processor,
    items=data,
    use_interpreters=True
):
    print(f"Result: {result}")
```

**Batch Processing:**
```python
# Process items in batches in parallel
batch_results = Parallel.process_batches(
    func=batch_processor,
    items=large_dataset,
    batch_size=100,
    use_interpreters=True
)
```

**Map-Reduce Operations:**
```python
def map_func(item):
    # Process item and return intermediate result
    return process_item(item)

def reduce_func(a, b):
    # Combine results
    return combine_results(a, b)

final_result = Parallel.reduce_parallel(
    map_func=map_func,
    reduce_func=reduce_func,
    items=dataset,
    use_interpreters=True,
    initial=initial_value
)
```

#### Smart Execution Methods

**Automatic Executor Selection:**
```python
# Smart map automatically chooses the best executor based on Python version and task type
results = Parallel.smart_map(
    func=cpu_intensive_function,
    items=data,
    task_type='cpu',  # 'cpu' or 'io'
    workers=Parallel.get_optimal_workers('cpu')
)

# Get optimal worker count based on system and Python version
optimal_workers = Parallel.get_optimal_workers(task_type='cpu')
```

#### Convenience Functions

All convenience functions now support interpreter pools:

```python
from nodupe.core.parallel import parallel_map, parallel_filter, parallel_partition, parallel_starmap

# Parallel mapping with interpreter support
results = parallel_map(
    func=processor,
    items=data,
    use_interpreters=True
)

# Parallel filtering
filtered = parallel_filter(
    predicate=is_duplicate,
    items=files,
    use_interpreters=True
)

# Parallel partitioning
cpu_items, io_items = parallel_partition(
    predicate=is_cpu_intensive,
    items=work_items,
    use_interpreters=True
)

# Parallel starmapping for functions with multiple arguments
results = parallel_starmap(
    func=process_with_params,
    args_list=[(arg1, arg2), (arg3, arg4)],
    use_interpreters=True
)

#### Progress Tracking

The `ParallelProgress` class provides thread-safe progress tracking for parallel operations:

```python
from nodupe.core.parallel import ParallelProgress

# Create progress tracker
progress = ParallelProgress(total=len(items))

# Use in parallel operations with thread-safe increment
def process_with_progress(item):
    result = process_item(item)
    progress.increment(success=True)  # Thread-safe increment
    return result

# Monitor progress in real-time
import time
while not progress.is_complete:
    completed, failed, percentage = progress.get_progress()
    print(f"Progress: {percentage:.1f}% ({completed} completed, {failed} failed)")
    time.sleep(1)
```

### Version Compatibility Matrix

| Python Version | Recommended Approach | Fallback |
|---------------|---------------------|----------|
| 3.12 | ProcessPoolExecutor | ThreadPoolExecutor |
| 3.13 (normal) | ProcessPoolExecutor | ThreadPoolExecutor |
| 3.13t (free-threaded) | ThreadPoolExecutor | ProcessPoolExecutor |
| 3.14+ | InterpreterPoolExecutor | ThreadPoolExecutor |
| 3.14t+ (free-threaded) | ThreadPoolExecutor | InterpreterPoolExecutor |

### Practical Usage Examples

Here are complete working examples that demonstrate the new parallel processing capabilities:

#### Example 1: Duplicate Detection with Parallel Processing

```python
from nodupe.core.parallel import Parallel, parallel_map
import hashlib

def calculate_file_hash(file_path):
    """Calculate hash for a file."""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None

def find_duplicates(file_paths):
    """Find duplicate files using parallel processing."""

    if Parallel.supports_interpreter_pool():
        # Python 3.14+: Use interpreter pools for maximum performance
        hashes = parallel_map(
            func=calculate_file_hash,
            items=file_paths,
            use_interpreters=True,
            workers=Parallel.get_optimal_workers('cpu')
        )
    elif Parallel.is_free_threaded():
        # Free-threaded Python: Use threads for CPU-bound work
        hashes = parallel_map(
            func=calculate_file_hash,
            items=file_paths,
            workers=Parallel.get_optimal_workers('cpu')
        )
    else:
        # Traditional Python: Use processes to bypass GIL
        hashes = parallel_map(
            func=calculate_file_hash,
            items=file_paths,
            use_processes=True,
            workers=Parallel.get_optimal_workers('cpu')
        )

    # Group files by hash to find duplicates
    hash_to_files = {}
    for path, hash_val in zip(file_paths, hashes):
        if hash_val:
            if hash_val not in hash_to_files:
                hash_to_files[hash_val] = []
            hash_to_files[hash_val].append(path)

    return {h: files for h, files in hash_to_files.items() if len(files) > 1}
```

#### Example 2: Smart Executor Selection

```python
from nodupe.core.parallel import Parallel

def process_large_dataset(data_items):
    """Process a large dataset using smart execution."""

    # Use smart_map for automatic executor selection
    results = Parallel.smart_map(
        func=process_item,
        items=data_items,
        task_type='cpu',  # or 'io' for I/O-bound tasks
        workers=Parallel.get_optimal_workers('cpu')
    )

    return results

def adaptive_batch_processing(large_dataset):
    """Process large datasets in batches with adaptive parallelism."""

    # Calculate optimal batch size based on Python capabilities
    optimal_workers = Parallel.get_optimal_workers('cpu')
    batch_size = max(10, len(large_dataset) // (optimal_workers * 2))

    batch_results = Parallel.process_batches(
        func=process_batch,
        items=large_dataset,
        batch_size=batch_size,
        use_interpreters=True if Parallel.supports_interpreter_pool() else False
    )

    return batch_results
```

#### Example 3: Progress Tracking and Error Handling

```python
from nodupe.core.parallel import Parallel, ParallelProgress

def robust_parallel_processing(items, processor_func):
    """Process items with progress tracking and error handling."""

    progress = ParallelProgress(total=len(items))
    successful_results = []
    failed_items = []

    # Process in parallel with progress tracking
    results_with_status = Parallel.process_in_parallel(
        func=lambda item: (processor_func(item), item, True),  # (result, item, success)
        items=items,
        use_interpreters=True if Parallel.supports_interpreter_pool() else False
    )

    for result, item, success in results_with_status:
        if success:
            successful_results.append(result)
            progress.increment(success=True)
        else:
            failed_items.append(item)
            progress.increment(success=False)

    return successful_results, failed_items
```

#### Example 4: Pool Optimization for Resource Management

```python
from nodupe.core.pools import Pools

def setup_optimized_infrastructure():
    """Set up optimized pools based on Python version."""

    # Create optimized pools that adapt to free-threaded vs GIL-locked Python
    worker_pool = Pools.create_worker_pool_optimized(
        workers=4,
        queue_size=100
    )

    connection_pool = Pools.create_connection_pool_optimized(
        connect_func=create_db_connection,
        max_connections=10
    )

    object_pool = Pools.create_pool_optimized(
        factory=create_processing_object,
        max_size=20
    )

    return worker_pool, connection_pool, object_pool
```

#### Optimization and Smart Execution Patterns

The NoDupeLabs parallel module includes several optimization patterns that automatically adapt to the Python environment:

**Automatic Worker Count Optimization:**
```python
# Get optimal worker count based on Python version and system capabilities
optimal_cpu_workers = Parallel.get_optimal_workers(task_type='cpu')
optimal_io_workers = Parallel.get_optimal_workers(task_type='io')

# Workers are automatically doubled in free-threaded mode for better utilization
print(f"Optimal CPU workers: {optimal_cpu_workers}")
```

**Smart Task Distribution:**
```python
def adaptive_processing_pipeline(data):
    """Use smart execution for optimal performance."""

    # Smart map automatically selects the best execution strategy
    return Parallel.smart_map(
        func=process_item,
        items=data,
        task_type='auto',  # Automatically detects CPU vs I/O bound
        workers=Parallel.get_optimal_workers('cpu')
    )
```

---

## 9. References and Resources

### Official Documentation
- [What's New in Python 3.13](https://docs.python.org/3/whatsnew/3.13.html)
- [What's New in Python 3.14](https://docs.python.org/3/whatsnew/3.14.html)
- [Python Free-Threading Guide](https://docs.python.org/3/howto/free-threading-python.html)
- [concurrent.futures Documentation](https://docs.python.org/3/library/concurrent.futures.html)

### PEPs (Python Enhancement Proposals)
- [PEP 684 – Per-Interpreter GIL](https://peps.python.org/pep-0684/)
- [PEP 703 – Making the GIL Optional](https://peps.python.org/pep-0703/)
- [PEP 734 – Multiple Interpreters in Stdlib](https://peps.python.org/pep-0734/)
- [PEP 744 – JIT Compilation](https://peps.python.org/pep-0744/)
- [PEP 779 – Free-Threading Support Criteria](https://peps.python.org/pep-0779/)

### Articles and Tutorials
- [Python 3.13: Free Threading and JIT](https://realpython.com/python313-free-threading-jit/)
- [Python 3.14 New Features](https://realpython.com/python314-new-features/)
- [Get Started with Free-Threaded Python 3.13](https://www.infoworld.com/article/3552750/get-started-with-the-free-threaded-build-of-python-3-13.html)
- [Python 3.14 Key Features and Updates](https://cloudsmith.com/blog/python-3-14-what-you-need-to-know)
- [Astral: Python 3.14 Overview](https://astral.sh/blog/python-3.14)

### Performance and Benchmarks
- [Speed Up Python with Concurrency](https://realpython.com/python-concurrency/)
- [Asyncio vs Concurrent Futures](https://medium.com/@nelsonchampion4real/asyncio-vs-concurrent-futures-in-python-choosing-the-right-concurrency-model-132e70d46a91)

---

## Summary

Python's threading landscape has evolved dramatically:

1. **Python 3.12**: Per-interpreter GIL enables parallel subinterpreters
2. **Python 3.13**: Experimental free-threading with ~40% overhead
3. **Python 3.14**: Production-ready free-threading with 5-10% overhead

**Key Takeaways**:
- Free-threading unlocks true CPU parallelism with threads
- Subinterpreters offer isolation with better efficiency than processes
- Choose the right tool: asyncio for I/O, free-threading/interpreters for CPU
- NoDupeLabs should detect Python version and optimize accordingly
- Thread safety becomes critical in free-threaded mode

**Future Outlook**:
- Python 3.15+: Further free-threading optimizations
- Ecosystem maturity: More libraries becoming thread-safe
- Performance improvements: Ongoing JIT and interpreter enhancements
