# Cascade-Autotune API Reference

## Overview

This document provides comprehensive API reference for the Cascade-Autotune Integration Framework, including all classes, methods, configuration options, and usage examples.

## Table of Contents

1. [Core Classes](#core-classes)
2. [Protocol and Base Classes](#protocol-and-base-classes)
3. [Plugin API](#plugin-api)
4. [Error Handling](#error-handling)
5. [Examples](#examples)

## Core Classes

### StageManager

Central orchestrator for all cascade stage operations.

```python
class StageManager:
    """Manager for cascade stages.
    
    Provides functionality to:
    - Register and discover cascade stages
    - Select optimal stages based on quality tiers
    - Handle stage execution and error recovery
    - Manage stage dependencies and availability
    """
    
    def __init__(self):
        """Initialize stage manager."""
    
    def register_stage(self, stage: CascadeStage) -> None:
        """Register a cascade stage.
        
        Args:
            stage: CascadeStage instance to register
        """
    
    def get_stage(self, stage_name: str) -> Optional[CascadeStage]:
        """Get a registered stage by name.
        
        Args:
            stage_name: Name of the stage to retrieve
            
        Returns:
            CascadeStage instance or None if not found
        """
    
    def get_available_stages(self) -> List[CascadeStage]:
        """Get all available stages.
        
        Returns:
            List of stages that can operate in current environment
        """
    
    def is_stage_available(self, stage_name: str) -> bool:
        """Check if a stage is available.
        
        Args:
            stage_name: Name of the stage to check
            
        Returns:
            True if stage is available, False otherwise
        """
    
    def select_optimal_stage(self, stage_type: str, quality_preference: QualityTier = QualityTier.BEST) -> Optional[CascadeStage]:
        """Select optimal stage based on quality preference.
        
        Args:
            stage_type: Type of stage to select
            quality_preference: Preferred quality tier
            
        Returns:
            Optimal stage instance or None if no suitable stage found
        """
    
    def execute_stage(self, stage_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute a stage with error handling.
        
        Args:
            stage_name: Name of the stage to execute
            *args: Arguments for the stage
            **kwargs: Keyword arguments for the stage
            
        Returns:
            Stage execution results
            
        Raises:
            StageExecutionError: If stage execution fails
        """
```

### ProgressiveHashingCascadeStage

Progressive hashing with algorithm cascading.

```python
class ProgressiveHashingCascadeStage(CascadeStage):
    """Progressive hashing cascade stage with algorithm cascading.
    
    This stage enhances existing ProgressiveHasher by implementing
    algorithm cascading that selects the optimal hashing algorithm based on:
    - Availability (BLAKE3, SHA256, MD5)
    - Security policy constraints
    - Performance requirements
    - Quality tier preferences
    
    The stage implements a three-phase progressive hashing approach:
    1. Size-based filtering (instant elimination)
    2. Quick hash comparison with algorithm cascade
    3. Full hash comparison with algorithm cascade
    """

    @property
    def name(self) -> str:
        """Stage name."""
        return "ProgressiveHashing"

    @property
    def quality_tier(self) -> QualityTier:
        """Quality tier for this stage."""
        return QualityTier.BEST

    @property
    def requires_internet(self) -> bool:
        """Whether this stage requires internet access."""
        return False

    @property
    def requires_plugins(self) -> List[str]:
        """List of required plugins."""
        return []

    def can_operate(self) -> bool:
        """Check if the stage can operate.
        
        Returns:
            True if the stage can operate (always True for progressive hashing)
        """
        return True

    def execute(self, files: List[Path]) -> Dict[str, Any]:
        """Execute progressive hashing with algorithm cascading.
        
        Args:
            files: List of file paths to hash and find duplicates
            
        Returns:
            Dictionary containing:
                - duplicates: List of duplicate file groups
                - quick_hash_algorithm: Algorithm used for quick hashing
                - full_hash_algorithm: Algorithm used for full hashing
                - files_processed: Number of files processed
                - duplicate_groups: Number of duplicate groups found
                - execution_time: Time taken for execution
                - algorithm_selection_reason: Reason for algorithm selection
                
        Raises:
            StageExecutionError: If execution fails
        """
```

### ArchiveProcessingCascadeStage

Archive processing with quality-tiered extraction.

```python
class ArchiveProcessingCascadeStage(CascadeStage):
    """Archive processing cascade stage with quality-tiered extraction.
    
    This stage enhances existing archive processing by implementing
    a cascaded approach to archive extraction that tries methods
    in order of quality and performance:
    1. 7z extraction (highest quality, best format support)
    2. zipfile extraction (good quality, standard ZIP support)
    3. tarfile extraction (acceptable quality, TAR/GZ support)
    """

    @property
    def name(self) -> str:
        """Stage name."""
        return "ArchiveProcessing"

    @property
    def quality_tier(self) -> QualityTier:
        """Quality tier for this stage."""
        return QualityTier.GOOD

    @property
    def requires_internet(self) -> bool:
        """Whether this stage requires internet access."""
        return False

    @property
    def requires_plugins(self) -> List[str]:
        """List of required plugins."""
        return ["py7zr"]  # 7z support is optional but preferred

    def can_operate(self) -> bool:
        """Check if the stage can operate.
        
        Returns:
            True if archive processing is allowed by security policy
        """
        return self._security_policy.allows_archive_processing()

    def execute(self, archive_path: Path) -> Dict[str, Any]:
        """Execute archive processing with cascaded extraction methods.
        
        Args:
            archive_path: Path to archive file to process
            
        Returns:
            Dictionary containing:
                - archive_path: Original archive path
                - extraction_results: List of extraction attempts
                - successful_method: Method that succeeded (or None)
                - total_files: Total number of files extracted
                - execution_time: Time taken for execution
                
        Raises:
            StageExecutionError: If execution fails
        """
```

### EnhancedScanPlugin

Enhanced scan plugin with Cascade integration.

```python
class EnhancedScanPlugin(Plugin):
    """Enhanced scan plugin with Cascade-Autotune integration.
    
    This plugin enhances the original ScanPlugin by integrating Cascade-Autotune
    stages for improved performance and intelligent algorithm selection.
    """

    name = "scan_enhanced"
    version = "2.0.0"
    dependencies = ["scan", "progressive_hashing_cascade", "archive_processing_cascade"]

    def initialize(self, container: Any) -> None:
        """Initialize the enhanced plugin."""
        # Check if cascade stages are available
        try:
            self.progressive_hashing_stage = get_progressive_hashing_stage()
            self.archive_processing_stage = get_archive_processing_stage()
            self.cascade_available = True
        except ImportError:
            self.cascade_available = False
            self.progressive_hashing_stage = None
            self.archive_processing_stage = None

    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        return {
            'commands': ['scan_enhanced'],
            'features': ['progressive_hashing_cascade', 'archive_processing_cascade', 'security_policy_integration']
        }

    def execute_enhanced_scan(self, args: argparse.Namespace) -> int:
        """Execute enhanced scan command with Cascade integration.
        
        Args:
            args: Command arguments including injected 'container'
        """
```

## Configuration API

### Configuration Schema

```yaml
# Complete configuration schema
cascade:
  enabled: boolean                    # Enable/disable cascade framework
  availability_ttl: number           # Availability cache TTL in seconds
  performance_monitoring: boolean    # Enable performance monitoring
  thread_monitoring: boolean         # Enable thread monitoring
  
  stages:
    hashing:                         # Hashing cascade configuration
      algorithms: [string]           # List of hash algorithms
      quality_tiers: [string]        # Quality tiers for algorithms
      fallback_timeout: number       # Timeout for fallback operations
    
    executor:                        # Executor cascade configuration
      types: [string]                # List of executor types
      quality_tiers: [string]        # Quality tiers for executors
      worker_limits: [number]        # Worker limits for each type
    
    archive:                         # Archive cascade configuration
      formats: [string]              # List of archive formats
      quality_tiers: [string]        # Quality tiers for formats

  thread_pool:
    max_workers: number              # Maximum number of workers
    monitoring_interval: number      # Monitoring interval in seconds
    degradation_threshold: number    # Performance degradation threshold
    worker_adjustment_cooldown: number # Worker adjustment cooldown
    overload_cpu_threshold: number   # CPU usage overload threshold
    overload_memory_threshold: number # Memory usage overload threshold

  performance:
    baseline_update_interval: number # Baseline update interval
    metrics_retention: number        # Metrics retention period
    alert_thresholds:                # Alert thresholds
      degradation: number            # Degradation alert threshold
      failure_rate: number           # Failure rate alert threshold
      response_time: number          # Response time alert threshold

  autotuning:
    sample_size: number              # Sample size for benchmarking
    iterations: number               # Number of benchmark iterations
    file_size_threshold: number      # File size threshold for recommendations
    memory_constrained: boolean      # Memory constraint flag
```

### Configuration Management

```python
class ConfigurationManager:
    def load_config(self, config_path: str = "nodupe.yml") -> Dict[str, Any]:
        """Load configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
    
    def get_cascade_config(self) -> Dict[str, Any]:
        """Get cascade-specific configuration"""
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration
        
        Args:
            updates: Dictionary of configuration updates
        """
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
```

## Plugin API

### Plugin Interface

```python
from nodupe.core.plugin_system.base import Plugin

class CascadeStagePlugin(Plugin):
    """Plugin interface for cascade stages"""
    
    @property
    def name(self) -> str:
        """Plugin name"""
    
    @property
    def version(self) -> str:
        """Plugin version"""
    
    @property
    def dependencies(self) -> List[str]:
        """List of plugin dependencies"""
    
    def initialize(self, container: Any) -> None:
        """Initialize the plugin
        
        Args:
            container: Dependency injection container
        """
    
    def shutdown(self) -> None:
        """Shutdown the plugin"""
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities
        
        Returns:
            Dictionary describing plugin capabilities
        """
    
    def get_cascade_stages(self) -> List[CascadeStage]:
        """Get cascade stages provided by this plugin
        
        Returns:
            List of cascade stage instances
        """
    
    def get_stage_requirements(self) -> Dict[str, int]:
        """Get thread/memory requirements for stages
        
        Returns:
            Dictionary mapping stage names to resource requirements
        """
```

### Plugin Development Example

```python
from nodupe.core.plugin_system.base import Plugin
from nodupe.core.cascade.stages.base import CascadeStage, QualityTier

class CustomHashStage(CascadeStage):
    def __init__(self):
        self._name = "CustomHash"
        self._quality_tier = QualityTier.BEST
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def quality_tier(self) -> QualityTier:
        return self._quality_tier
    
    def can_operate(self) -> bool:
        # Check if custom hash algorithm is available
        try:
            import custom_hash_lib
            return True
        except ImportError:
            return False
    
    def execute(self, file_path: str) -> str:
        import custom_hash_lib
        with open(file_path, 'rb') as f:
            data = f.read()
        return custom_hash_lib.custom_hash(data)

class CustomHashPlugin(Plugin):
    def __init__(self):
        self._name = "custom_hash_plugin"
        self._version = "1.0.0"
        self._dependencies = []
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def dependencies(self) -> List[str]:
        return self._dependencies
    
    def initialize(self, container: Any) -> None:
        # Register custom cascade stage
        custom_stage = CustomHashStage()
        cascade_manager = container.get_service('cascade_manager')
        cascade_manager.register_stage(custom_stage)
    
    def shutdown(self) -> None:
        # Cleanup resources if needed
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "cascade_stages": ["custom_hash"],
            "algorithms": ["custom_hash"],
            "description": "Provides custom hash algorithm for enhanced performance"
        }
    
    def get_cascade_stages(self) -> List[CascadeStage]:
        return [CustomHashStage()]
    
    def get_stage_requirements(self) -> Dict[str, int]:
        return {
            "custom_hash": {
                "threads": 2,
                "memory_mb": 100
            }
        }
```

## Monitoring API

### Performance Monitor

```python
class PerformanceMonitor:
    def __init__(self, cascade_manager: CascadeManager, 
                 thread_monitor: ThreadPoolMonitor):
        """Initialize performance monitor
        
        Args:
            cascade_manager: Cascade manager instance
            thread_monitor: Thread pool monitor instance
        """
    
    def monitor(self, operation_name: str) -> ContextManager:
        """Create performance monitoring context
        
        Args:
            operation_name: Name of operation to monitor
            
        Returns:
            Context manager for monitoring
        """
    
    def get_metrics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics
        
        Args:
            operation_name: Specific operation or None for all
            
        Returns:
            Dictionary with performance metrics
        """
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get active performance alerts"""
    
    def clear_alerts(self) -> None:
        """Clear all performance alerts"""
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format
        
        Args:
            format: Export format (json, csv, etc.)
            
        Returns:
            Exported metrics as string
        """
```

### Monitoring Context Manager

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def monitor_operation(operation_name: str, 
                     performance_monitor: PerformanceMonitor) -> Generator[Dict[str, Any], None, None]:
    """Context manager for operation monitoring
    
    Args:
        operation_name: Name of operation to monitor
        performance_monitor: Performance monitor instance
        
    Yields:
        Dictionary to store operation results
    """
    start_time = time.monotonic()
    metrics = {
        'operation': operation_name,
        'start_time': start_time,
        'success': False
    }
    
    try:
        yield metrics
        metrics['success'] = True
    except Exception as e:
        metrics['success'] = False
        metrics['error'] = str(e)
        raise
    finally:
        end_time = time.monotonic()
        metrics['duration'] = end_time - start_time
        performance_monitor.record_metrics(metrics)
```

## Error Handling

### Exception Hierarchy

```python
class CascadeError(Exception):
    """Base exception for cascade framework"""

class ConfigurationError(CascadeError):
    """Configuration-related errors"""

class StageExecutionError(CascadeError):
    """Stage execution failures"""

class ComponentInitializationError(CascadeError):
    """Component initialization failures"""

class PerformanceDegradationError(CascadeError):
    """Performance degradation detected"""

class ResourceExhaustionError(CascadeError):
    """System resource exhaustion"""

class PluginError(CascadeError):
    """Plugin-related errors"""

class PluginLoadError(PluginError):
    """Plugin loading failures"""

class PluginDependencyError(PluginError):
    """Plugin dependency resolution failures"""
```

### Error Handling Examples

```python
def robust_cascade_operation(cascade_manager: CascadeManager, 
                           operation_name: str, *args, **kwargs):
    """Execute cascade operation with comprehensive error handling"""
    
    try:
        # Attempt cascade execution
        result = cascade_manager.execute_cascade(operation_name, *args, **kwargs)
        return result
    
    except StageExecutionError as e:
        # Stage-specific error - log and continue
        logging.warning(f"Stage execution failed: {e}")
        # System automatically falls back to next stage
        
    except ConfigurationError as e:
        # Configuration error - use defaults
        logging.error(f"Configuration error: {e}")
        # Fall back to standard operation
        
    except ResourceExhaustionError as e:
        # Resource exhaustion - reduce load
        logging.error(f"Resource exhaustion: {e}")
        # Reduce worker count, batch size, etc.
        
    except Exception as e:
        # Unexpected error - log and continue
        logging.error(f"Unexpected error: {e}")
        # System continues with standard operation

def handle_plugin_errors(plugin_manager: PluginManager):
    """Handle plugin-related errors gracefully"""
    
    try:
        plugin_manager.load_plugins()
    except PluginLoadError as e:
        logging.warning(f"Plugin loading failed: {e}")
        # Continue without problematic plugins
    except PluginDependencyError as e:
        logging.warning(f"Plugin dependency error: {e}")
        # Skip plugins with missing dependencies
    except Exception as e:
        logging.error(f"Plugin system error: {e}")
        # Disable plugin system entirely
```

## Examples

### Basic Usage Example

```python
from nodupe.core.container import container
from nodupe.core.cascade.manager import CascadeManager

def basic_cascade_usage():
    """Basic cascade usage example"""
    
    # Get cascade manager from container
    cascade_manager = container.get_service('cascade_manager')
    
    # Execute hashing with cascade
    file_path = "/path/to/file.txt"
    file_hash = cascade_manager.execute_cascade("hashing", file_path)
    print(f"File hash: {file_hash}")
    
    # Execute batch processing
    file_paths = ["/path/to/file1.txt", "/path/to/file2.txt"]
    results = cascade_manager.execute_cascade("executor", process_files, file_paths)
    print(f"Processed {len(results)} files")
    
    # Check cascade status
    status = cascade_manager.get_cascade_status()
    print(f"Cascade status: {status}")

def process_files(file_paths: List[str]) -> List[Dict[str, Any]]:
    """Process multiple files"""
    results = []
    for file_path in file_paths:
        # Process each file
        result = process_single_file(file_path)
        results.append(result)
    return results

def process_single_file(file_path: str) -> Dict[str, Any]:
    """Process a single file"""
    return {
        'path': file_path,
        'processed': True,
        'timestamp': time.time()
    }
```

### Advanced Configuration Example

```python
def advanced_configuration():
    """Advanced configuration example"""
    
    config = {
        'cascade': {
            'enabled': True,
            'availability_ttl': 60.0,
            'performance_monitoring': True,
            'thread_monitoring': True,
            
            'stages': {
                'hashing': {
                    'algorithms': ['blake3', 'sha512', 'sha256', 'md5'],
                    'quality_tiers': ['best', 'good', 'acceptable', 'minimal'],
                    'fallback_timeout': 5.0
                },
                'executor': {
                    'types': ['interpreter', 'thread', 'process'],
                    'quality_tiers': ['best', 'good', 'acceptable'],
                    'worker_limits': [8, 16, 4]
                }
            },
            
            'thread_pool': {
                'max_workers': 32,
                'monitoring_interval': 10,
                'degradation_threshold': 1.5,
                'worker_adjustment_cooldown': 30,
                'overload_cpu_threshold': 90,
                'overload_memory_threshold': 85
            },
            
            'performance': {
                'baseline_update_interval': 60,
                'metrics_retention': 3600,
                'alert_thresholds': {
                    'degradation': 2.0,
                    'failure_rate': 0.1,
                    'response_time': 10.0
                }
            },
            
            'autotuning': {
                'sample_size': 1024 * 1024,
                'iterations': 10,
                'file_size_threshold': 10 * 1024 * 1024,
                'memory_constrained': False
            }
        }
    }
    
    return config
```

### Plugin Development Example

```python
def create_custom_plugin():
    """Complete plugin development example"""
    
    from nodupe.core.plugin_system.base import Plugin
    from nodupe.core.cascade.stages.base import CascadeStage, QualityTier
    
    class CustomExecutorStage(CascadeStage):
        def __init__(self):
            self._name = "CustomExecutor"
            self._quality_tier = QualityTier.GOOD
        
        @property
        def name(self) -> str:
            return self._name
        
        @property
        def quality_tier(self) -> QualityTier:
            return self._quality_tier
        
        def can_operate(self) -> bool:
            # Check if custom executor is available
            try:
                import custom_executor
                return True
            except ImportError:
                return False
        
        def execute(self, func, items, **kwargs):
            import custom_executor
            return custom_executor.execute(func, items, **kwargs)
    
    class CustomExecutorPlugin(Plugin):
        def __init__(self):
            self._name = "custom_executor_plugin"
            self._version = "1.0.0"
            self._dependencies = []
        
        @property
        def name(self) -> str:
            return self._name
        
        @property
        def version(self) -> str:
            return self._version
        
        @property
        def dependencies(self) -> List[str]:
            return self._dependencies
        
        def initialize(self, container: Any) -> None:
            # Register custom executor stage
            custom_stage = CustomExecutorStage()
            cascade_manager = container.get_service('cascade_manager')
            cascade_manager.register_stage(custom_stage)
        
        def shutdown(self) -> None:
            pass
        
        def get_capabilities(self) -> Dict[str, Any]:
            return {
                "cascade_stages": ["custom_executor"],
                "executors": ["custom"],
                "description": "Provides custom executor for specialized workloads"
            }
        
        def get_cascade_stages(self) -> List[CascadeStage]:
            return [CustomExecutorStage()]
    
    return CustomExecutorPlugin()
```

### Monitoring and Alerting Example

```python
def monitoring_example():
    """Monitoring and alerting example"""
    
    from nodupe.core.cascade.monitoring.performance import PerformanceMonitor
    
    # Get performance monitor
    performance_monitor = container.get_service('performance_monitor')
    
    # Monitor specific operation
    with performance_monitor.monitor("file_processing") as monitor:
        # Perform operation
        result = process_large_files(file_list)
        
        # Store results
        monitor['files_processed'] = len(file_list)
        monitor['result'] = result
    
    # Get performance summary
    summary = performance_monitor.get_summary()
    print(f"Average response time: {summary['avg_response_time']:.3f}s")
    print(f"Success rate: {summary['success_rate']:.2%}")
    print(f"Throughput: {summary['throughput']:.2f} files/sec")
    
    # Check for alerts
    alerts = performance_monitor.get_alerts()
    if alerts:
        print("Performance alerts:")
        for alert in alerts:
            print(f"  - {alert['type']}: {alert['message']}")
    
    # Export metrics
    metrics_json = performance_monitor.export_metrics("json")
    with open("performance_metrics.json", "w") as f:
        f.write(metrics_json)
```

### Error Handling Example

```python
def error_handling_example():
    """Comprehensive error handling example"""
    
    from nodupe.core.cascade.errors import (
        StageExecutionError, ConfigurationError, 
        ResourceExhaustionError
    )
    
    try:
        # Attempt cascade operation
        result = cascade_manager.execute_cascade("hashing", file_path)
        return result
    
    except StageExecutionError as e:
        logging.warning(f"Stage execution failed: {e}")
        # Try alternative approach
        return fallback_hashing(file_path)
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        # Use default configuration
        return default_hashing(file_path)
    
    except ResourceExhaustionError as e:
        logging.error(f"Resource exhaustion: {e}")
        # Reduce resource usage and retry
        reduce_resource_usage()
        return cascade_manager.execute_cascade("hashing", file_path)
    
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        # Fall back to standard operation
        return standard_hashing(file_path)

def fallback_hashing(file_path: str) -> str:
    """Fallback hashing implementation"""
    import hashlib
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def default_hashing(file_path: str) -> str:
    """Default hashing implementation"""
    return fallback_hashing(file_path)

def standard_hashing(file_path: str) -> str:
    """Standard hashing implementation"""
    return fallback_hashing(file_path)

def reduce_resource_usage():
    """Reduce resource usage"""
    thread_monitor = container.get_service('thread_monitor')
    if thread_monitor:
        current_workers = thread_monitor.get_max_workers()
        new_workers = max(2, current_workers // 2)
        thread_monitor.set_max_workers(new_workers)
```

## Conclusion

This API reference provides comprehensive documentation for the Cascade-Autotune Integration Framework. The framework is designed to be:

- **Extensible**: Easy to add new cascade stages and plugins
- **Configurable**: Highly configurable for different environments
- **Monitorable**: Comprehensive monitoring and alerting capabilities
- **Resilient**: Robust error handling and graceful degradation
- **User-friendly**: Clear APIs and comprehensive documentation

By following these API patterns and examples, developers can effectively integrate and extend the Cascade-Autotune framework for their specific needs.
