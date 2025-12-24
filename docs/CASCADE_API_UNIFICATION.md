# Cascade-Autotune API Unification

## Overview

This document describes the unified API design for the Cascade-Autotune integration with NoDupesLab, ensuring consistency with the existing plugin architecture while providing enhanced functionality.

## API Architecture

### Core Components

#### 1. Plugin System Integration

**Base Plugin Interface** (`nodupe/core/plugin_system/base.py`)
```python
class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def version(self) -> str: ...
    
    @property
    @abstractmethod
    def dependencies(self) -> List[str]: ...
    
    @abstractmethod
    def initialize(self, container: Any) -> None: ...
    
    @abstractmethod
    def shutdown(self) -> None: ...
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]: ...
```

**Enhanced Plugin Pattern** (follows base interface)
```python
class EnhancedScanPlugin(Plugin):
    name = "scan_enhanced"
    version = "2.0.0"
    dependencies = ["scan", "progressive_hashing_cascade", "archive_processing_cascade"]
    
    def initialize(self, container: Any) -> None:
        # Initialize cascade stages
        self.progressive_hashing_stage = get_progressive_hashing_stage()
        self.archive_processing_stage = get_archive_processing_stage()
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'commands': ['scan_enhanced'],
            'features': ['progressive_hashing_cascade', 'archive_processing_cascade']
        }
```

#### 2. Cascade Stage Protocol

**Stage Interface** (`nodupe/core/cascade/protocol.py`)
```python
class CascadeStage(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def quality_tier(self) -> QualityTier: ...
    
    @property
    @abstractmethod
    def requires_internet(self) -> bool: ...
    
    @property
    @abstractmethod
    def requires_plugins(self) -> List[str]: ...
    
    @abstractmethod
    def can_operate(self) -> bool: ...
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]: ...
```

**Stage Implementation Pattern**
```python
class ProgressiveHashingCascadeStage(CascadeStage):
    @property
    def name(self) -> str:
        return "ProgressiveHashing"
    
    @property
    def quality_tier(self) -> QualityTier:
        return QualityTier.BEST
    
    def can_operate(self) -> bool:
        return True  # Always available
    
    def execute(self, files: List[Path]) -> Dict[str, Any]:
        # Implementation with algorithm cascading
        return {
            "duplicates": [...],
            "quick_hash_algorithm": "blake3",
            "full_hash_algorithm": "blake3",
            "files_processed": len(files),
            "duplicate_groups": count,
            "execution_time": time
        }
```

### API Consistency Patterns

#### 1. Error Handling

**Unified Error Types**
```python
# Stage execution errors
from nodupe.core.cascade.protocol import StageExecutionError

try:
    result = stage.execute(files)
except StageExecutionError as e:
    print(f"Stage {e.stage} failed: {e.message}")
    print(f"Execution time: {e.execution_time}")

# Plugin errors (existing pattern)
try:
    result = plugin.execute_scan(args)
except Exception as e:
    print(f"Plugin {plugin.name} failed: {e}")
```

#### 2. Configuration and Feature Detection

**Environment Detection**
```python
from nodupe.core.cascade.environment import EnvironmentDetector

# Check plugin availability
if EnvironmentDetector.check_plugin_available("blake3"):
    use_blake3 = True

# Check security policy
from nodupe.core.security.policy import SecurityPolicy
if SecurityPolicy().allows_algorithm("sha256"):
    use_sha256 = True
```

**Quality Tier Selection**
```python
from nodupe.core.cascade.protocol import QualityTier, get_stage_manager

# Get optimal stage by quality preference
manager = get_stage_manager()
stage = manager.select_optimal_stage("ProgressiveHashing", QualityTier.BEST)
```

#### 3. Performance Measurement

**Built-in Performance Tracking**
```python
# All cascade stages include execution time
result = stage.execute(files)
execution_time = result["execution_time"]

# Performance comparison
blake3_time = blake3_result["execution_time"]
sha256_time = sha256_result["execution_time"]
improvement = (sha256_time - blake3_time) / sha256_time * 100
```

### Integration Patterns

#### 1. Plugin-to-Stage Integration

**Enhanced Plugin Pattern**
```python
class EnhancedScanPlugin(Plugin):
    def execute_enhanced_scan(self, args: argparse.Namespace) -> int:
        # 1. Determine strategy
        use_cascade = args.cascade and self.cascade_available
        
        # 2. Execute with appropriate method
        if use_cascade:
            return self._execute_cascade_scan(args)
        else:
            return self._execute_original_scan(args)
    
    def _execute_cascade_scan(self, args: argparse.Namespace) -> int:
        # Use cascade stages
        hash_result = self.progressive_hashing_stage.execute(files)
        archive_result = self.archive_processing_stage.execute(archives)
        
        # Process results
        return self._process_cascade_results(hash_result, archive_result)
```

#### 2. Stage-to-Stage Coordination

**Cascaded Execution**
```python
def execute_cascade_workflow(files: List[Path]) -> Dict[str, Any]:
    # 1. Archive processing
    archive_stage = get_archive_processing_stage()
    archive_results = {}
    for archive in archive_files:
        archive_results[archive] = archive_stage.execute(archive)
    
    # 2. Progressive hashing
    hash_stage = get_progressive_hashing_stage()
    hash_result = hash_stage.execute(non_archive_files)
    
    # 3. Combine results
    return {
        "archive_processing": archive_results,
        "progressive_hashing": hash_result,
        "total_files": len(files),
        "execution_time": sum(r.get("execution_time", 0) for r in archive_results.values()) + hash_result.get("execution_time", 0)
    }
```

### Backward Compatibility

#### 1. Plugin Compatibility

**Original Plugin Interface Preserved**
```python
# Original ScanPlugin still works
from nodupe.plugins.commands.scan import ScanPlugin
original_plugin = ScanPlugin()
original_plugin.execute_scan(args)  # No changes required

# Enhanced plugin provides additional features
from nodupe.plugins.commands.scan_enhanced import EnhancedScanPlugin
enhanced_plugin = EnhancedScanPlugin()
enhanced_plugin.execute_enhanced_scan(args)  # New enhanced features
```

#### 2. Database Compatibility

**Existing Database Schema**
```python
# FileRepository interface unchanged
from nodupe.core.database.files import FileRepository

# Both original and enhanced plugins use same interface
file_repo = FileRepository(db_connection)
file_repo.batch_add_files(files)  # Works with both
file_repo.get_duplicate_files()   # Works with both
```

#### 3. Command Line Interface

**Backward Compatible Commands**
```bash
# Original command (unchanged)
python -m nodupe scan /path/to/directory

# Enhanced command (new features)
python -m nodupe scan_enhanced /path/to/directory --cascade --algorithm auto

# Both commands work in the same system
```

### Error Recovery and Fallback

#### 1. Stage Fallback Strategy

**Automatic Fallback**
```python
def execute_with_fallback(stage_name: str, *args, **kwargs):
    try:
        # Try best quality stage
        stage = get_stage_manager().select_optimal_stage(stage_name, QualityTier.BEST)
        return stage.execute(*args, **kwargs)
    except StageExecutionError:
        # Fall back to original method
        return execute_original_method(*args, **kwargs)
```

#### 2. Plugin Fallback Strategy

**Graceful Degradation**
```python
class EnhancedScanPlugin(Plugin):
    def execute_enhanced_scan(self, args: argparse.Namespace) -> int:
        try:
            if self.cascade_available and args.cascade:
                return self._execute_cascade_scan(args)
            else:
                return self._execute_original_scan(args)
        except Exception as e:
            # Log error and fall back
            print(f"Cascade failed, falling back to original: {e}")
            return self._execute_original_scan(args)
```

### Performance Monitoring

#### 1. Built-in Metrics

**Stage Performance Tracking**
```python
# All stages include performance metrics
result = stage.execute(files)
metrics = {
    "stage_name": stage.name,
    "quality_tier": stage.quality_tier.value,
    "execution_time": result["execution_time"],
    "files_processed": result["files_processed"],
    "algorithm_used": result.get("quick_hash_algorithm", "unknown")
}
```

#### 2. Plugin Performance Tracking

**Enhanced Plugin Metrics**
```python
class EnhancedScanPlugin(Plugin):
    def get_performance_metrics(self) -> Dict[str, Any]:
        return {
            "cascade_enabled": self.cascade_enabled,
            "cascade_available": self.cascade_available,
            "performance_improvement": self._calculate_improvement(),
            "stage_metrics": self._get_stage_metrics()
        }
```

### Security Integration

#### 1. Security Policy Integration

**Consistent Security Checks**
```python
# All stages respect security policy
from nodupe.core.security.policy import SecurityPolicy

class ProgressiveHashingCascadeStage(CascadeStage):
    def can_operate(self) -> bool:
        return self._security_policy.allows_algorithm("sha256")
    
    def _get_optimal_full_hasher(self) -> ProgressiveHasher:
        if self._security_policy.allows_algorithm("sha256"):
            return ProgressiveHasher()
        else:
            return ProgressiveHasherMD5()  # Fallback
```

#### 2. Archive Processing Security

**Secure Archive Handling**
```python
class ArchiveProcessingCascadeStage(CascadeStage):
    def can_operate(self) -> bool:
        return self._security_policy.allows_archive_processing()
    
    def execute(self, archive_path: Path) -> Dict[str, Any]:
        # Security validation before processing
        if not self._security_policy.validate_archive(archive_path):
            raise StageExecutionError("Archive security validation failed", stage=self.name)
        
        # Process with security checks
        return super().execute(archive_path)
```

## Usage Examples

### Basic Usage

```python
# Register cascade stages
from nodupe.core.cascade.stages.progressive_hashing import ProgressiveHashingCascadeStage
from nodupe.core.cascade.stages.archive_processing import ArchiveProcessingCascadeStage

register_stage(ProgressiveHashingCascadeStage())
register_stage(ArchiveProcessingCascadeStage())

# Use enhanced plugin
from nodupe.plugins.commands.scan_enhanced import EnhancedScanPlugin
plugin = EnhancedScanPlugin()
plugin.execute_enhanced_scan(args)
```

### Advanced Usage

```python
# Direct stage usage
from nodupe.core.cascade.protocol import get_stage_manager

manager = get_stage_manager()

# Get optimal stage
stage = manager.select_optimal_stage("ProgressiveHashing", QualityTier.BEST)

# Execute with performance tracking
result = manager.execute_stage("ProgressiveHashing", files)
print(f"Processed {result['files_processed']} files in {result['execution_time']:.3f}s")
print(f"Algorithm used: {result['quick_hash_algorithm']}")
```

### Error Handling

```python
try:
    result = execute_stage("ProgressiveHashing", files)
    print(f"Success: {result['duplicate_groups']} duplicate groups found")
except StageExecutionError as e:
    print(f"Stage failed: {e.message}")
    print(f"Stage: {e.stage}, Time: {e.execution_time}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Migration Guide

### For Plugin Developers

1. **Extend existing plugins** rather than replacing them
2. **Follow the existing plugin interface** exactly
3. **Add cascade integration** as optional enhancement
4. **Maintain backward compatibility** with original functionality

### For Stage Developers

1. **Inherit from CascadeStage** for consistent interface
2. **Implement quality tiers** for optimal selection
3. **Include error handling** with StageExecutionError
4. **Provide performance metrics** in results

### For System Integrators

1. **Register stages globally** using `register_stage()`
2. **Use stage manager** for optimal stage selection
3. **Handle fallbacks gracefully** when stages unavailable
4. **Monitor performance** using built-in metrics

## Conclusion

The unified API design ensures that Cascade-Autotune integration:

- **Maintains full backward compatibility** with existing plugins
- **Provides consistent interfaces** across all components
- **Enables easy extension** for new stages and plugins
- **Supports graceful degradation** when dependencies unavailable
- **Includes comprehensive error handling** and performance monitoring
- **Integrates seamlessly** with existing security policies

This design allows for incremental adoption and ensures that the enhanced functionality works alongside the existing system without disruption.
