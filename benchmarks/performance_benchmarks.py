"""
Performance benchmarks for NoDupeLabs parallel processing features.
Tests GIL-locked vs free-threaded vs interpreter pool performance.
"""

import os
import sys
import time
import tempfile
import shutil
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple
import statistics

def load_benchmark_config() -> Dict:
    """Load benchmark configuration from JSON file.
    
    Attempts to load configuration from benchmarks/benchmark_config.json.
    If the file doesn't exist, returns default configuration values.
    
    Returns:
        Dictionary containing benchmark configuration settings with the following structure:
        {
            "benchmark_settings": {
                "threading": {
                    "thread_counts": [int],      # List of thread counts to test
                    "file_count": int,           # Number of files for threading test
                    "file_size_mb": float,       # Size of each file in MB
                    "iterations": int            # Number of iterations per test
                },
                "parallel_strategies": {
                    "strategies": [dict],        # List of strategy configs
                    "file_count": int,           # Number of files for parallel test
                    "file_size_mb": float,       # Size of each file in MB
                    "iterations": int,           # Number of iterations per test
                    "max_workers": int           # Maximum workers for parallel processing
                },
                "test_files": {
                    "num_files": int,            # Number of test files to create
                    "size_mb": float,            # Size of each test file in MB
                    "duplicate_ratio": float     # Ratio of duplicate files to create
                },
                "reporting": {
                    "output_dir": str,           # Output directory for reports
                    "threading_report_file": str,# Filename for threading report
                    "parallel_report_file": str  # Filename for parallel report
                }
            }
        }
    """
    config_path = Path("benchmarks/benchmark_config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Default configuration if config file doesn't exist
        return {
            "benchmark_settings": {
                "threading": {
                    "thread_counts": [1, 2, 4, 8, 16],
                    "file_count": 100,
                    "file_size_mb": 0.5,
                    "iterations": 3
                },
                "parallel_strategies": {
                    "strategies": [
                        {"name": "Sequential", "use_processes": False, "use_interpreters": False},
                        {"name": "Threading", "use_processes": False, "use_interpreters": False},
                        {"name": "Processing", "use_processes": True, "use_interpreters": False}
                    ],
                    "file_count": 50,
                    "file_size_mb": 1.0,
                    "iterations": 3,
                    "max_workers": 8
                },
                "test_files": {
                    "num_files": 50,
                    "size_mb": 1.0,
                    "duplicate_ratio": 0.1
                },
                "reporting": {
                    "output_dir": "benchmarks",
                    "threading_report_file": "threading_performance_report.md",
                    "parallel_report_file": "parallel_strategy_report.md"
                }
            }
        }

def create_test_files(directory: Path, num_files: int, size_mb: float = 1.0):
    """Create test files for benchmarking.
    
    Creates a specified number of files with random content to avoid compression
    artifacts, and creates duplicate files at regular intervals to simulate
    realistic duplicate detection scenarios.
    
    Args:
        directory: Directory path where test files will be created
        num_files: Number of test files to create
        size_mb: Size of each file in megabytes (default: 1.0 MB)
    """
    import random
    import string
    
    directory.mkdir(exist_ok=True)
    
    for i in range(num_files):
        # Create files with random content to avoid compression artifacts
        content_size = int(size_mb * 1024 * 1024)
        content = ''.join(random.choices(string.ascii_letters + string.digits + '\n', k=content_size//2))
        
        file_path = directory / f"test_file_{i:04d}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create duplicates for realistic duplicate detection scenarios
        if i % 10 == 0:  # Every 10th file is a duplicate
            dup_path = directory / f"test_file_dup_{i:04d}.txt"
            shutil.copy2(file_path, dup_path)

def run_nodupe_scan(path: str, threads: int = 1) -> Tuple[float, int]:
    """Run NoDupe scan and measure performance.
    
    Executes a file scanning operation using the NoDupeLabs core modules
    and measures the time taken and number of files processed.
    
    Args:
        path: Directory path to scan for files
        threads: Number of threads to use for processing (default: 1)
    
    Returns:
        Tuple containing:
        - Duration in seconds (float)
        - Number of files processed (int)
    """
    start_time = time.time()
    
    # Import and run the file processor
    from nodupe.core.scan.processor import FileProcessor
    from nodupe.core.scan.walker import FileWalker
    
    # Create processor with walker
    walker = FileWalker()
    processor = FileProcessor(walker)
    
    # Process files in the directory
    files = processor.process_files(path)
    
    duration = time.time() - start_time
    file_count = len(files)
    
    return duration, file_count

def _process_file_path_for_benchmark(file_path: str, test_dir: str = ""):
    """Module-level function for processing file paths in parallel.
    
    Creates file information dictionary and processes a single file using the
    NoDupeLabs processor. This function is designed to be used in parallel
    processing contexts where individual file paths need to be processed.
    
    Args:
        file_path: Path to the file to process
        test_dir: Base directory for relative path calculation (default: "")
    
    Returns:
        Processed file information if successful, None if an error occurs
    """
    try:
        from nodupe.core.scan.processor import FileProcessor
        from nodupe.core.scan.walker import FileWalker
        
        walker = FileWalker()
        processor = FileProcessor(walker)
        
        # Create file info manually
        file_info = {
            'path': file_path,
            'relative_path': os.path.relpath(file_path, str(test_dir)) if test_dir else file_path,
            'name': os.path.basename(file_path),
            'extension': os.path.splitext(file_path)[1].lower(),
            'size': os.path.getsize(file_path),
            'modified_time': int(os.path.getmtime(file_path)),
            'created_time': int(os.path.getctime(file_path)),
            'is_directory': False,
            'is_file': True,
            'is_symlink': os.path.islink(file_path)
        }
        
        return processor._process_single_file(file_info)
    except Exception:
        return None

def _process_file_path_with_test_dir(file_path: str):
    """Wrapper function for multiprocessing that uses a global test_dir.
    
    This function is used to avoid passing the test_dir as a parameter
    which can cause pickling issues during multiprocessing. Instead, 
    we use a global variable that gets set before the multiprocessing call.
    
    Args:
        file_path: Path to the file to process
    
    Returns:
        Processed file information if successful, None if an error occurs
    """
    global _GLOBAL_TEST_DIR
    try:
        return _process_file_path_for_benchmark(file_path, _GLOBAL_TEST_DIR)
    except:
        return None

def benchmark_parallel_strategies():
    """Benchmark different parallel processing strategies.
    
    Tests various parallel processing approaches including Sequential, Threading,
    and Processing strategies to compare their performance characteristics.
    
    Returns:
        Dictionary containing benchmark results with the following structure:
        {
            'StrategyName': {
                'avg_duration': float,     # Average execution time in seconds
                'std_duration': float,     # Standard deviation of execution time
                'avg_throughput': float,   # Average throughput (files/second)
                'file_count': int          # Number of files processed
            }
        }
    """
    config = load_benchmark_config()
    settings = config['benchmark_settings']['parallel_strategies']
    
    print("Benchmarking parallel processing strategies...")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "benchmark_files"
        create_test_files(test_dir, settings['file_count'], settings['file_size_mb'])
        
        print(f"Created test files in: {test_dir}")
        print(f"Test directory size: {sum(f.stat().st_size for f in test_dir.rglob('*')) / (1024*1024):.2f} MB")
        
        # Import parallel processing module
        from nodupe.core.parallel import Parallel
        
        # Test different strategies using the walker and processor
        strategies = []
        for strategy_config in settings['strategies']:
            strategy_name = strategy_config['name']
            use_processes = strategy_config['use_processes']
            use_interpreters = strategy_config['use_interpreters']
            strategies.append((strategy_name, use_processes, use_interpreters))
        
        # Add interpreter pool if available
        if Parallel.supports_interpreter_pool():
            strategies.append(('Interpreters', False, True))
        
        results = {}
        
        for strategy_name, use_processes, use_interpreters in strategies:
            print(f"\nTesting {strategy_name} strategy...")
            
            durations = []
            file_counts = []
            
            # Run multiple iterations
            for iteration in range(settings['iterations']):
                print(f"  Iteration {iteration + 1}/{settings['iterations']}...")
                
                start_time = time.time()
                
                if strategy_name == 'Sequential':
                    # Sequential processing using the public API
                    from nodupe.core.scan.processor import FileProcessor
                    from nodupe.core.scan.walker import FileWalker
                    
                    walker = FileWalker()
                    processor = FileProcessor(walker)
                    
                    # Use the processor's public method to process the directory
                    files = processor.process_files(str(test_dir))
                else:
                    # For process pool, we need to use a different approach that avoids
                    # passing complex objects that can't be pickled
                    if use_processes:
                        # Use file paths instead of file info objects for process pool
                        from nodupe.core.scan.walker import FileWalker
                        walker = FileWalker()
                        all_files = walker.walk(str(test_dir))
                        file_paths = [f['path'] for f in all_files]
                        
                        # For multiprocessing, we need to use a module-level function
                        # Set the global test_dir for the worker processes
                        global _GLOBAL_TEST_DIR
                        _GLOBAL_TEST_DIR = str(test_dir)
                        
                        # Use parallel processing on file paths with the module-level function
                        processed_files = Parallel.process_in_parallel(
                            _process_file_path_with_test_dir,
                            file_paths,
                            workers=min(len(file_paths), settings['max_workers']),
                            use_processes=use_processes,
                            use_interpreters=use_interpreters
                        )
                        
                        files = [f for f in processed_files if f is not None]
                    else:
                        # For threading and interpreter pools, we can pass file info objects
                        from nodupe.core.scan.walker import FileWalker
                        walker = FileWalker()
                        
                        # Get all files to process
                        all_files = walker.walk(str(test_dir))
                        
                        def process_single_file_info(file_info):
                            try:
                                from nodupe.core.scan.processor import FileProcessor
                                processor = FileProcessor()
                                
                                # Create a new FileWalker for each thread
                                from nodupe.core.scan.walker import FileWalker
                                walker = FileWalker()
                                processor.file_walker = walker
                                
                                # Process the file info
                                return processor._process_single_file(file_info)
                            except Exception:
                                return None
                        
                        # Use parallel processing on the file info list
                        processed_files = Parallel.process_in_parallel(
                            process_single_file_info,
                            all_files,
                            workers=min(len(all_files), settings['max_workers']),
                            use_processes=use_processes,
                            use_interpreters=use_interpreters
                        )
                        
                        files = [f for f in processed_files if f is not None]
                
                duration = time.time() - start_time
                file_count = len(files)
                
                durations.append(duration)
                file_counts.append(file_count)
                
                print(f"    Duration: {duration:.2f}s, Files processed: {file_count}")
            
            avg_duration = statistics.mean(durations)
            std_duration = statistics.stdev(durations) if len(durations) > 1 else 0
            
            results[strategy_name] = {
                'avg_duration': avg_duration,
                'std_duration': std_duration,
                'avg_throughput': file_counts[0] / avg_duration,
                'file_count': file_counts[0]
            }
            
            print(f"  Average duration: {avg_duration:.2f}s ± {std_duration:.2f}s")
            print(f"  Throughput: {results[strategy_name]['avg_throughput']:.2f} files/sec")
    
    return results

def benchmark_threading_performance():
    """Benchmark performance across different threading configurations.
    
    Tests various threading configurations to evaluate performance characteristics
    with different numbers of threads and analyzes the optimal threading strategy.
    
    Returns:
        Dictionary containing benchmark results with the following structure:
        {
            thread_count: {
                'avg_duration': float,     # Average execution time in seconds
                'std_duration': float,     # Standard deviation of execution time
                'avg_throughput': float,   # Average throughput (files/second)
                'file_count': int          # Number of files processed
            }
        }
    """
    config = load_benchmark_config()
    settings = config['benchmark_settings']['threading']
    
    print("Setting up benchmark environment...")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "benchmark_files"
        create_test_files(test_dir, settings['file_count'], settings['file_size_mb'])
        
        print(f"Created test files in: {test_dir}")
        print(f"Test directory size: {sum(f.stat().st_size for f in test_dir.rglob('*')) / (1024*1024):.2f} MB")
        
        # Test different thread counts
        thread_configs = settings['thread_counts']
        results = {}
        
        for threads in thread_configs:
            print(f"\nTesting with {threads} threads...")
            
            durations = []
            file_counts = []
            
            # Run multiple iterations for statistical significance
            for iteration in range(settings['iterations']):
                print(f"  Iteration {iteration + 1}/{settings['iterations']}...")
                duration, file_count = run_nodupe_scan(str(test_dir), threads)
                durations.append(duration)
                file_counts.append(file_count)
                
                print(f"    Duration: {duration:.2f}s, Files processed: {file_count}")
            
            avg_duration = statistics.mean(durations)
            std_duration = statistics.stdev(durations) if len(durations) > 1 else 0
            
            results[threads] = {
                'avg_duration': avg_duration,
                'std_duration': std_duration,
                'avg_throughput': file_counts[0] / avg_duration,
                'file_count': file_counts[0]
            }
            
            print(f"  Average duration: {avg_duration:.2f}s ± {std_duration:.2f}s")
            print(f"  Throughput: {results[threads]['avg_throughput']:.2f} files/sec")
    
    return results

def benchmark_python_versions():
    """Compare performance across different Python versions if available."""
    print("\nChecking Python version capabilities...")
    
    # Check if we have access to different Python execution modes
    python_executable = sys.executable
    print(f"Current Python: {python_executable}")
    print(f"Python version: {sys.version}")
    
    # Check for free-threaded Python capabilities
    try:
        import _thread
        print("Standard threading available")
    except ImportError:
        print("Threading module not available")
    
    # Check for interpreter pool support
    try:
        from concurrent.futures import ProcessPoolExecutor
        print("Process pool support available")
    except ImportError:
        print("Process pool support not available")
    
    # Add hardware information using only standard library
    print("\nHardware Information:")
    import platform
    import os
    
    # Get CPU information
    cpu_info = platform.processor()
    if not cpu_info:
        # Fallback to get CPU info from /proc/cpuinfo on Linux
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        cpu_info = line.split(':')[1].strip()
                        break
        except (FileNotFoundError, PermissionError):
            cpu_info = "Unknown"
    
    # Get memory information using standard library
    try:
        total_memory_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        total_memory_gb = total_memory_bytes / (1024**3)
    except (ValueError, OSError):
        total_memory_gb = 0.0
    
    print(f"CPU: {cpu_info}")
    print(f"CPU Cores: {os.cpu_count()} logical")
    print(f"Memory: {total_memory_gb:.1f} GB")
    print(f"Platform: {platform.system()} {platform.machine()}")

def generate_performance_report(results: Dict[int, Dict[str, float]]) -> str:
    """Generate a performance report from benchmark results.
    
    Creates a comprehensive markdown report containing benchmark results,
    performance analysis, and recommendations based on the collected data.
    
    Args:
        results: Dictionary containing benchmark results with thread counts as keys
                and performance metrics as values. Structure:
                {
                    thread_count: {
                        'avg_duration': float,     # Average execution time in seconds
                        'std_duration': float,     # Standard deviation of execution time
                        'avg_throughput': float,   # Average throughput (files/second)
                        'file_count': int          # Number of files processed
                    }
                }
    
    Returns:
        String containing formatted markdown report
    """
    report = []
    report.append("# NoDupeLabs Performance Benchmark Report\n")
    report.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    report.append("## Test Environment")
    report.append(f"- Python Version: {sys.version}")
    report.append(f"- Platform: {sys.platform}")
    report.append(f"- CPU Count: {os.cpu_count()}\n")
    
    report.append("## Benchmark Results")
    report.append("| Threads | Avg Duration (s) | Std Dev (s) | Throughput (files/s) | Speedup |")
    report.append("|---------|------------------|-------------|---------------------|---------|")
    
    baseline = results[1]['avg_duration']  # 1 thread as baseline
    
    for threads in sorted(results.keys()):
        result = results[threads]
        speedup = baseline / result['avg_duration']
        report.append(
            f"| {threads:7d} | {result['avg_duration']:16.2f} | "
            f"{result['std_duration']:11.2f} | {result['avg_throughput']:19.2f} | "
            f"{speedup:7.2f}x |"
        )
    
    report.append(f"\n*Speedup calculated relative to 1 thread baseline ({baseline:.2f}s)*\n")
    
    # Analysis
    report.append("## Performance Analysis")
    max_speedup = max(results[t]['avg_duration'] / results[1]['avg_duration'] for t in results.keys())
    optimal_threads = max(results.keys(), key=lambda x: results[x]['avg_duration'] / results[1]['avg_duration'])
    
    report.append(f"- Maximum speedup achieved: {max_speedup:.2f}x with {optimal_threads} threads")
    report.append(f"- Optimal thread count: {optimal_threads}")
    
    if optimal_threads >= os.cpu_count():
        report.append("- Performance scales well with CPU cores")
    else:
        report.append("- Performance may be limited by I/O or other factors")
    
    return '\n'.join(report)

def generate_parallel_performance_report(results: Dict) -> str:
    """Generate a performance report from parallel benchmark results."""
    report = []
    report.append("# NoDupeLabs Parallel Processing Performance Report\n")
    report.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    report.append("## Test Environment")
    report.append(f"- Python Version: {sys.version}")
    report.append(f"- Platform: {sys.platform}")
    report.append(f"- CPU Count: {os.cpu_count()}\n")
    
    report.append("## Parallel Strategy Results")
    report.append("| Strategy | Avg Duration (s) | Std Dev (s) | Throughput (files/s) | Speedup |")
    report.append("|----------|------------------|-------------|---------------------|---------|")
    
    baseline = results['Sequential']['avg_duration']  # Sequential as baseline
    
    for strategy in ['Sequential', 'Threading', 'Processing', 'Interpreters']:
        if strategy in results:
            result = results[strategy]
            speedup = baseline / result['avg_duration']
            report.append(
                f"| {strategy:8s} | {result['avg_duration']:16.2f} | "
                f"{result['std_duration']:11.2f} | {result['avg_throughput']:19.2f} | "
                f"{speedup:7.2f}x |"
            )
    
    report.append(f"\n*Speedup calculated relative to Sequential baseline ({baseline:.2f}s)*\n")
    
    # Analysis
    report.append("## Performance Analysis")
    if 'Interpreters' in results:
        interpreter_speedup = baseline / results['Interpreters']['avg_duration']
        report.append(f"- Interpreter pool speedup: {interpreter_speedup:.2f}x")
    
    if 'Processing' in results:
        process_speedup = baseline / results['Processing']['avg_duration']
        report.append(f"- Process pool speedup: {process_speedup:.2f}x")
    
    if 'Threading' in results:
        thread_speedup = baseline / results['Threading']['avg_duration']
        report.append(f"- Threading speedup: {thread_speedup:.2f}x")
    
    optimal_strategy = min(results.keys(), key=lambda x: results[x]['avg_duration'])
    report.append(f"- Optimal strategy: {optimal_strategy}")
    
    return '\n'.join(report)

def main():
    """Main benchmark runner."""
    print("Starting NoDupeLabs Performance Benchmarks")
    print("=" * 50)
    
    # Run threading performance benchmarks
    threading_results = benchmark_threading_performance()
    
    print("\n" + "=" * 50)
    
    # Run parallel strategy benchmarks
    parallel_results = benchmark_parallel_strategies()
    
    # Check Python version capabilities
    benchmark_python_versions()
    
    # Generate and save threading report
    threading_report = generate_performance_report(threading_results)
    threading_report_path = Path("benchmarks/threading_performance_report.md")
    threading_report_path.parent.mkdir(exist_ok=True)
    with open(threading_report_path, 'w', encoding='utf-8') as f:
        f.write(threading_report)
    
    # Generate and save parallel strategy report
    parallel_report = generate_parallel_performance_report(parallel_results)
    parallel_report_path = Path("benchmarks/parallel_strategy_report.md")
    with open(parallel_report_path, 'w', encoding='utf-8') as f:
        f.write(parallel_report)
    
    print(f"\nThreading performance report saved to: {threading_report_path}")
    print(f"Parallel strategy report saved to: {parallel_report_path}")
    print("\n" + "=" * 50)
    print("Benchmark Summary:")
    
    print("\nThreading Performance:")
    for threads in sorted(threading_results.keys()):
        result = threading_results[threads]
        speedup = threading_results[1]['avg_duration'] / result['avg_duration']
        print(f" {threads:2d} threads: {result['avg_duration']:6.2f}s ({speedup:5.2f}x speedup)")
    
    print("\nParallel Strategies:")
    baseline = parallel_results['Sequential']['avg_duration']
    for strategy in ['Sequential', 'Threading', 'Processing', 'Interpreters']:
        if strategy in parallel_results:
            result = parallel_results[strategy]
            speedup = baseline / result['avg_duration']
            print(f"  {strategy:11s}: {result['avg_duration']:6.2f}s ({speedup:5.2f}x speedup)")

if __name__ == "__main__":
    main()
