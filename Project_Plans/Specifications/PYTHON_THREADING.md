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

Based on our parallel processing modules (`parallel.py`, `pools.py`), here are recommended updates:

### Current Implementation

Our current implementation uses:
- ✅ `ThreadPoolExecutor` for I/O-bound tasks
- ✅ `ProcessPoolExecutor` for CPU-bound tasks
- ✅ Thread-safe pools and queues
- ✅ Proper resource cleanup with context managers

### Recommended Enhancements

#### 1. Add Free-Threading Detection

```python
import sys

class Parallel:
    @staticmethod
    def is_free_threaded() -> bool:
        """Check if running in free-threaded mode."""
        return hasattr(sys, 'flags') and getattr(sys.flags, 'gil', 1) == 0

    @staticmethod
    def get_optimal_workers() -> int:
        """Get optimal worker count based on Python version."""
        if Parallel.is_free_threaded():
            # Free-threaded: use more threads for CPU work
            return cpu_count() * 2
        else:
            # GIL present: conservative thread count
            return min(32, cpu_count())
```

#### 2. Add InterpreterPoolExecutor Support (Python 3.14+)

```python
from concurrent.futures import InterpreterPoolExecutor

class Parallel:
    @staticmethod
    def map_with_interpreters(func, items, workers=None):
        """Map using subinterpreters (Python 3.14+)."""
        if sys.version_info >= (3, 14):
            with InterpreterPoolExecutor(max_interpreters=workers) as executor:
                return list(executor.map(func, items))
        else:
            # Fallback to ProcessPoolExecutor
            return Parallel.map_parallel(func, items, workers, use_processes=True)
```

#### 3. Smart Executor Selection

```python
class Parallel:
    @staticmethod
    def smart_map(func, items, task_type='auto', workers=None):
        """
        Intelligently choose executor based on:
        - Python version
        - Task type (CPU/IO)
        - Free-threading availability
        """
        if task_type == 'auto':
            # Auto-detect based on function inspection
            task_type = 'cpu' if is_cpu_bound(func) else 'io'

        if task_type == 'cpu':
            if sys.version_info >= (3, 14):
                # Use InterpreterPoolExecutor
                return map_with_interpreters(func, items, workers)
            elif Parallel.is_free_threaded():
                # Use threads in free-threaded mode
                return map_parallel(func, items, workers, use_processes=False)
            else:
                # Use processes (traditional approach)
                return map_parallel(func, items, workers, use_processes=True)
        else:  # I/O-bound
            # Always use threads for I/O
            return map_parallel(func, items, workers, use_processes=False)
```

### Version Compatibility Matrix

| Python Version | Recommended Approach | Fallback |
|---------------|---------------------|----------|
| 3.12 | ProcessPoolExecutor | ThreadPoolExecutor |
| 3.13 (normal) | ProcessPoolExecutor | ThreadPoolExecutor |
| 3.13t (free-threaded) | ThreadPoolExecutor | ProcessPoolExecutor |
| 3.14+ | InterpreterPoolExecutor | ProcessPoolExecutor |
| 3.14t+ (free-threaded) | ThreadPoolExecutor | InterpreterPoolExecutor |

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
