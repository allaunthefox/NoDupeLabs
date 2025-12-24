# Cascade-Autotune Failure Modes & Recovery Guide

## Overview

This guide documents all possible failure modes of the Cascade-Autotune framework and provides detailed recovery procedures. Understanding these failure modes ensures reliable operation and quick recovery when issues occur.

## Failure Mode Categories

### 1. **Complete Framework Failure**
### 2. **Partial Component Failure**
### 3. **Configuration Failures**
### 4. **Performance Degradation**
### 5. **User-Initiated Disable**

## 1. Complete Framework Failure

### **Symptoms**
- All cascade services unavailable
- System falls back to standard NoDupesLab operation
- Performance degradation of 20-30%
- No cascade-related log entries

### **Causes**
- Import errors for cascade modules
- System resource detection failures
- Container initialization failures
- Critical configuration errors

### **Detection**

```bash
# Check cascade status
nodupe status --cascade

# Expected output for complete failure:
# [WARNING] Cascade Manager: Unavailable
# [WARNING] Thread Monitor: Unavailable
# [WARNING] Hash Autotuner: Unavailable
# [WARNING] Adaptive Processor: Unavailable
# [INFO] System operating in standard mode
```

### **Recovery Procedures**

#### **Automatic Recovery**
The system automatically falls back to standard operation:

```python
# System automatically:
# 1. Skips all cascade initialization
# 2. Uses standard library threading
# 3. Uses conservative hash algorithm selection
# 4. Uses standard file processing pipeline
# 5. Maintains full NoDupesLab functionality
```

#### **Manual Recovery**

```bash
# 1. Check for import errors
python -c "from nodupe.core.cascade.manager import CascadeManager; print('OK')"

# 2. Check system resources
python -c "import psutil; print(f'CPU: {psutil.cpu_count()}, RAM: {psutil.virtual_memory().total / (1024**3):.1f}GB')"

# 3. Reset configuration
cp nodupe.yml nodupe.yml.backup
echo "cascade:\n  enabled: true" > nodupe.yml

# 4. Restart with debug logging
export NODUPE_DEBUG=1
nodupe scan --root /path/to/files --verbose
```

#### **Forced Recovery**

```bash
# 1. Disable cascade temporarily
echo "cascade:\n  enabled: false" > recovery.yml
nodupe --config recovery.yml scan --root /path/to/files

# 2. Fix underlying issues
# - Check Python version compatibility
# - Verify system resources
# - Fix configuration errors

# 3. Re-enable cascade
echo "cascade:\n  enabled: true" > nodupe.yml
nodupe scan --root /path/to/files
```

## 2. Partial Component Failure

### **Thread Monitor Failure**

**Symptoms**:
- Thread pool monitoring unavailable
- Static worker allocation
- No performance-based worker adjustment

**Causes**:
- psutil import failure
- System monitoring permission issues
- Resource detection errors

**Recovery**:

```python
# Check thread monitor status
thread_monitor = container.get_service('thread_monitor')
if thread_monitor is None:
    print("Thread monitor failed - using standard threading")
    # System automatically uses standard library threading
```

**Configuration Fix**:

```yaml
# Force standard threading
cascade:
  thread_monitoring: false
  thread_pool:
    max_workers: 8  # Fixed worker count
```

### **Hash Autotuner Failure**

**Symptoms**:
- No algorithm optimization
- Conservative algorithm selection
- No performance benchmarking

**Causes**:
- Optional dependency missing (blake3, xxhash)
- Benchmarking errors
- File system access issues

**Recovery**:

```python
# Check autotuner status
tuner = container.get_service('hash_autotuner')
if tuner is None:
    print("Autotuner failed - using conservative defaults")
    # System automatically uses SHA-256
```

**Configuration Fix**:

```yaml
# Force specific algorithm
cascade:
  autotuning:
    enabled: false
    default_algorithm: sha256
```

### **Plugin Loading Failure**

**Symptoms**:
- Some cascade plugins not loaded
- Missing cascade stages
- Reduced optimization capabilities

**Causes**:
- Plugin import errors
- Dependency resolution failures
- Circular dependency issues

**Recovery**:

```bash
# Check plugin status
nodupe status --plugins

# Reload plugins
nodupe plugins reload

# Check specific plugin
nodupe plugins info cascade-hash-plugin
```

**Configuration Fix**:

```yaml
# Disable problematic plugins
plugins:
  loading_order: [
    "core",
    "database",
    "scan",        # Skip cascade plugins
    "similarity",
    "apply",
    "plan"
  ]
```

## 3. Configuration Failures

### **Invalid Configuration Syntax**

**Symptoms**:
- Configuration parsing errors
- Service initialization failures
- System startup issues

**Common Errors**:

```yaml
# WRONG - Invalid syntax
cascade:
  stages: "blake3, sha256"  # Should be list
  thread_pool: "max_workers: 16"  # Should be object

# CORRECT - Valid syntax
cascade:
  stages: ["blake3", "sha256"]
  thread_pool:
    max_workers: 16
```

**Recovery**:

```bash
# Validate configuration
nodupe config validate

# Fix syntax errors
nodupe config fix

# Use backup configuration
cp nodupe.yml.backup nodupe.yml
```

### **Invalid Configuration Values**

**Symptoms**:
- Runtime errors during operation
- Performance issues
- Unexpected behavior

**Common Issues**:

```yaml
# WRONG - Invalid values
cascade:
  thread_pool:
    max_workers: 0  # Must be positive
    monitoring_interval: -1  # Must be positive
  performance:
    degradation_threshold: 0.5  # Too low, causes false positives

# CORRECT - Valid values
cascade:
  thread_pool:
    max_workers: 16
    monitoring_interval: 10
  performance:
    degradation_threshold: 1.5
```

**Recovery**:

```bash
# Check configuration values
nodupe config check-values

# Reset to defaults
nodupe config reset-defaults

# Validate specific sections
nodupe config validate cascade.thread_pool
```

### **Missing Dependencies**

**Symptoms**:
- Import errors for optional dependencies
- Reduced functionality
- Fallback to conservative defaults

**Common Missing Dependencies**:

```bash
# Check for BLAKE3
python -c "import blake3; print('BLAKE3 available')" || echo "BLAKE3 missing"

# Check for xxHash
python -c "import xxhash; print('xxHash available')" || echo "xxHash missing"

# Check for psutil
python -c "import psutil; print('psutil available')" || echo "psutil missing"
```

**Recovery**:

```bash
# Install missing dependencies
pip install blake3 xxhash psutil

# Or configure to work without them
cascade:
  autotuning:
    memory_constrained: true  # Use conservative defaults
  thread_monitoring: false    # Disable if psutil unavailable
```

## 4. Performance Degradation

### **High Resource Usage**

**Symptoms**:
- High CPU usage
- High memory usage
- System slowdown
- Timeout errors

**Diagnosis**:

```python
# Check resource usage
import psutil
print(f"CPU: {psutil.cpu_percent()}%")
print(f"Memory: {psutil.virtual_memory().percent}%")

# Check cascade performance
performance_monitor = container.get_service('performance_monitor')
summary = performance_monitor.get_summary()
print(f"Response time: {summary['avg_response_time']:.3f}s")
print(f"Success rate: {summary['success_rate']:.2%}")
```

**Recovery**:

```yaml
# Reduce resource usage
cascade:
  thread_pool:
    max_workers: 4  # Reduce workers
    monitoring_interval: 30  # Less frequent monitoring
  performance:
    baseline_update_interval: 300  # Slower updates
    alert_thresholds:
      response_time: 30.0  # Higher threshold
      degradation: 3.0     # Higher threshold
```

### **Slow Performance**

**Symptoms**:
- Slower than expected processing
- Long operation times
- User complaints about speed

**Diagnosis**:

```python
# Check performance metrics
performance_monitor = container.get_service('performance_monitor')
summary = performance_monitor.get_summary()

# Compare with baseline
if summary['avg_response_time'] > baseline_response_time * 2:
    print("Performance significantly degraded")
```

**Recovery**:

```yaml
# Optimize for performance
cascade:
  stages:
    hashing:
      algorithms: ["blake3"]  # Use fastest algorithm only
  thread_pool:
    max_workers: 32  # Increase workers
    monitoring_interval: 5   # More frequent monitoring
  performance:
    degradation_threshold: 1.1  # Stricter threshold
```

### **Inconsistent Performance**

**Symptoms**:
- Variable processing times
- Unpredictable behavior
- Intermittent failures

**Causes**:
- Resource contention
- System load variations
- Network issues (for remote operations)

**Recovery**:

```yaml
# Stabilize performance
cascade:
  thread_pool:
    worker_adjustment_cooldown: 60  # Slower adjustments
    overload_cpu_threshold: 70     # Lower threshold
    overload_memory_threshold: 70  # Lower threshold
  performance:
    baseline_update_interval: 180  # Slower baseline updates
    metrics_retention: 7200        # Longer retention
```

## 5. User-Initiated Disable

### **Explicit Disable via Configuration**

**Symptoms**:
- cascade.enabled = false in configuration
- No cascade services initialized
- Standard NoDupesLab operation

**User Intent**:
- Simplified debugging
- Reduced complexity
- Performance testing
- Troubleshooting

**Recovery**:

```yaml
# Re-enable cascade
cascade:
  enabled: true
  availability_ttl: 30.0
  performance_monitoring: true
  thread_monitoring: true
```

### **Runtime Disable**

**Symptoms**:
- Cascade services stopped during operation
- System continues with standard operation
- No immediate errors

**Recovery**:

```python
# Check if cascade is disabled
cascade_disabled = container.get_service('cascade_disabled')
if cascade_disabled:
    print("Cascade explicitly disabled by user")
    # No action needed - user intended this behavior
```

## Monitoring and Prevention

### **Health Checks**

```python
def check_cascade_health():
    """Comprehensive cascade health check"""
    
    health_status = {
        'cascade_manager': False,
        'thread_monitor': False,
        'hash_autotuner': False,
        'adaptive_processor': False,
        'performance_monitor': False
    }
    
    # Check each component
    for service_name in health_status:
        service = container.get_service(service_name)
        health_status[service_name] = service is not None
    
    # Overall health
    overall_health = all(health_status.values())
    
    return {
        'healthy': overall_health,
        'components': health_status,
        'recommendations': get_health_recommendations(health_status)
    }

def get_health_recommendations(health_status):
    """Get recommendations based on health status"""
    recommendations = []
    
    if not health_status['thread_monitor']:
        recommendations.append("Thread monitor failed - check psutil installation")
    
    if not health_status['hash_autotuner']:
        recommendations.append("Hash autotuner failed - check optional dependencies")
    
    if not health_status['cascade_manager']:
        recommendations.append("Cascade manager failed - check configuration")
    
    return recommendations
```

### **Automated Recovery**

```python
def automated_recovery():
    """Automated recovery for common issues"""
    
    health = check_cascade_health()
    
    if not health['healthy']:
        print("Cascade health issues detected, attempting recovery...")
        
        # Try to restart failed components
        for component, healthy in health['components'].items():
            if not healthy:
                try:
                    restart_component(component)
                    print(f"Restarted {component}")
                except Exception as e:
                    print(f"Failed to restart {component}: {e}")
        
        # Check health after recovery
        new_health = check_cascade_health()
        if new_health['healthy']:
            print("Recovery successful")
        else:
            print("Manual intervention required")
            print("Recommendations:", new_health['recommendations'])

def restart_component(component_name):
    """Restart a specific cascade component"""
    # Implementation depends on component type
    pass
```

### **Preventive Measures**

```yaml
# Preventive configuration
cascade:
  health_check_interval: 300  # Check health every 5 minutes
  auto_recovery_enabled: true # Enable automatic recovery
  backup_config_enabled: true # Keep backup configurations
  log_level: "INFO"          # Appropriate logging level
  
  # Conservative defaults for stability
  thread_pool:
    max_workers: 16
    monitoring_interval: 20
    degradation_threshold: 2.0
  
  performance:
    baseline_update_interval: 120
    alert_thresholds:
      degradation: 2.5
      failure_rate: 0.05
      response_time: 15.0
```

## Emergency Procedures

### **Complete System Reset**

```bash
# 1. Stop all operations
pkill -f nodupe

# 2. Backup current state
cp nodupe.yml nodupe.yml.emergency-backup
cp -r logs logs.emergency-backup

# 3. Reset to minimal configuration
cat > nodupe.yml << EOF
cascade:
  enabled: false
database:
  path: output/index.db
log_dir: logs
plugins:
  auto_load: false
EOF

# 4. Restart with minimal configuration
nodupe scan --root /path/to/files --config nodupe.yml

# 5. Gradually re-enable features
# - Test basic functionality first
# - Re-enable cascade incrementally
# - Monitor for issues
```

### **Configuration Rollback**

```bash
# 1. Check for backup configurations
ls -la *.backup

# 2. Rollback to last known good configuration
cp nodupe.yml.backup nodupe.yml

# 3. Validate configuration
nodupe config validate

# 4. Restart with rolled-back configuration
nodupe scan --root /path/to/files
```

### **Component Isolation**

```bash
# 1. Disable specific components
cat > isolated.yml << EOF
cascade:
  enabled: true
  performance_monitoring: false  # Disable performance monitoring
  thread_monitoring: false       # Disable thread monitoring
  stages:
    hashing: ["sha256"]          # Use only standard algorithms
    executor: ["thread"]         # Use only standard executors
EOF

# 2. Test with isolated components
nodupe --config isolated.yml scan --root /path/to/files

# 3. Gradually re-enable components
# - Enable one component at a time
# - Test after each enablement
# - Monitor for issues
```

## Conclusion

Understanding and preparing for failure modes ensures reliable operation of the Cascade-Autotune framework. The key principles are:

1. **Graceful Degradation**: System continues working even when cascade fails
2. **Automatic Recovery**: Many issues resolve themselves automatically
3. **Manual Recovery**: Clear procedures for manual intervention when needed
4. **Prevention**: Monitoring and preventive measures reduce failure likelihood
5. **User Control**: Users can disable cascade features when needed

By following this guide, you can maintain reliable operation and quickly recover from any issues that occur.
