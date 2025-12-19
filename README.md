# NoDupeLabs

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/allaunthefox/NoDupeLabs/actions)

⚠️ **WARNING: This is an LLM-generated project. The authors explicitly disavow and disclaim ALL responsibility for ANY outcome, good or bad, resulting from the use of this code. This includes but is not limited to: data loss, security breaches, system failures, financial losses, legal issues, or any other damages. The codebase is an unwieldy monster with unpredictable behaviors and inherent security/logic risks. By using this code, you acknowledge that you assume COMPLETE and SOLE responsibility for all risks and consequences. The authors shall not be held liable for any claims, damages, or other liabilities arising from or related to the use of this software, regardless of the form of action. USE AT YOUR OWN EXTREME PERIL.**

## 📖 Overview

NoDupeLabs is a sophisticated file deduplication and similarity detection system built with Python. This project provides advanced capabilities for identifying duplicate files, managing metadata, and maintaining efficient file storage systems through intelligent caching and parallel processing.

## 🚀 Features

### Core Functionality
- **Advanced File Deduplication**: Intelligent duplicate file detection using multiple algorithms
- **Similarity Analysis**: Sophisticated similarity scoring and clustering
- **Plugin Architecture**: Extensible plugin system for custom similarity commands
- **Incremental Processing**: Efficient handling of large file collections
- **Parallel Processing**: Multi-threaded operations for optimal performance

### Technical Highlights
- **Plugin System**: Dynamic plugin discovery and hot-reload capabilities
- **Database Management**: Robust transaction handling and schema management
- **Caching System**: Multi-level caching (hash, embedding, query) for performance
- **Time Synchronization**: Built-in time sync utilities for accurate timestamps
- **Security Features**: Comprehensive security measures and validation
- **Memory Management**: Efficient memory usage with configurable limits

### Advanced Features
- **Archive Support**: Handles various archive formats (ZIP, TAR, etc.)
- **GPU Acceleration**: Optional GPU support for compute-intensive operations
- **Network Integration**: Time synchronization and network-aware operations
- **Video Processing**: Specialized video file handling and analysis
- **ML Integration**: Machine learning capabilities for similarity detection

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Git

### Basic Installation
```bash
# Clone the repository
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# Install dependencies
pip install -e .

# Run initial setup
nodupe init
```

### Development Installation
```bash
# Clone and install with development dependencies
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# Install with development tools
pip install -e ".[dev]"

# Run tests
pytest
```

## 🎯 Quick Start

### Basic Usage
```bash
# Scan a directory for duplicates
nodupe scan /path/to/your/files

# Find similar files
nodupe similarity /path/to/your/files

# Apply deduplication rules
nodupe apply /path/to/your/files
```

### Programmatic Usage
```python
from nodupe.core.api import NoDupeAPI

# Initialize the API
api = NoDupeAPI()

# Scan for duplicates
results = api.scan_directory("/path/to/files")

# Get similarity clusters
clusters = api.find_similar_files(results)

# Apply deduplication
api.apply_deduplication(clusters)
```

## 🏗️ Architecture

### Core Components

```
nodupe/
├── core/                    # Core functionality
│   ├── api.py             # Main API interface
│   ├── config.py          # Configuration management
│   ├── plugins.py         # Plugin system
│   ├── parallel.py        # Parallel processing
│   ├── security.py        # Security features
│   └── time_sync_utils.py # Time synchronization
├── database/               # Database operations
│   ├── database.py        # Database interface
│   ├── schema.py          # Database schema
│   └── transactions.py    # Transaction management
├── cache/                  # Caching system
│   ├── hash_cache.py      # Hash caching
│   ├── embedding_cache.py # Embedding caching
│   └── query_cache.py     # Query caching
├── scan/                   # File scanning
│   ├── walker.py          # File system walker
│   ├── progress.py        # Progress tracking
│   └── hash_autotune.py   # Hash optimization
└── plugin_system/          # Plugin architecture
    ├── registry.py        # Plugin registry
    ├── discovery.py       # Plugin discovery
    └── hot_reload.py      # Hot reload support
```

### Plugin System

NoDupeLabs features a powerful plugin system that allows for extensibility:

```python
from nodupe.core.plugins import SimilarityCommandPlugin

class MyCustomPlugin(SimilarityCommandPlugin):
    def __init__(self):
        super().__init__()
        self.name = "my_custom_similarity"
        self.description = "Custom similarity detection algorithm"
    
    def calculate_similarity(self, file1, file2):
        # Your custom logic here
        return similarity_score
```

## 🔧 Configuration

### Environment Variables
```bash
# Database configuration
NODUPE_DB_PATH=/path/to/database.db
NODUPE_DB_TIMEOUT=30.0

# Cache configuration
NODUPE_CACHE_SIZE=1000
NODUPE_CACHE_TTL=3600

# Performance tuning
NODUPE_MAX_THREADS=4
NODUPE_MEMORY_LIMIT=1024

# Time synchronization
NODUPE_TIMESYNC_ENABLED=true
NODUPE_TIMESYNC_SERVERS=time.google.com,time.cloudflare.com
```

### Configuration File
Create a `nodupe.yaml` file:
```yaml
database:
  path: /path/to/database.db
  timeout: 30.0

cache:
  size: 1000
  ttl: 3600

performance:
  max_threads: 4
  memory_limit: 1024

timesync:
  enabled: true
  servers:
    - time.google.com
    - time.cloudflare.com
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/core/          # Core functionality tests
pytest tests/plugins/       # Plugin system tests
pytest tests/integration/   # Integration tests

# Run with coverage
pytest --cov=nodupe --cov-report=html
```

### Performance Testing
```bash
# Run performance benchmarks
python benchmarks/performance_benchmarks.py

# Test parallel processing
python benchmarks/parallel_strategy_report.py

# Memory usage analysis
python tests/utils/performance.py
```

## 📊 Performance

### Benchmarks
- **File Processing**: Up to 10,000 files/minute
- **Memory Usage**: Configurable limits with intelligent caching
- **Parallel Processing**: Multi-threaded with configurable thread pools
- **Database Performance**: Optimized queries with transaction batching

### Optimization Tips
1. **Adjust thread count** based on your CPU cores
2. **Configure cache sizes** based on available memory
3. **Use incremental processing** for large datasets
4. **Enable GPU acceleration** for ML operations when available

## 🤖 Plugins

### Built-in Plugins
- **Leap Year**: Date handling utilities
- **Time Sync**: Time synchronization utilities
- **Video Processing**: Video file analysis
- **ML Similarity**: Machine learning-based similarity detection

### Installing Plugins
```bash
# Install a plugin
nodupe plugin install plugin-name

# List installed plugins
nodupe plugin list

# Enable/disable plugins
nodupe plugin enable plugin-name
nodupe plugin disable plugin-name
```

## 🔒 Security

### Security Features
- **Input Validation**: Comprehensive input sanitization
- **File Validation**: Malicious file detection
- **Database Security**: Transaction safety and rollback
- **Memory Protection**: Bounds checking and overflow prevention
- **Network Security**: Secure time synchronization

### Best Practices
1. **Regular Updates**: Keep the system updated
2. **Input Validation**: Always validate external inputs
3. **Access Control**: Limit database access permissions
4. **Audit Logs**: Monitor system activities
5. **Backup Strategy**: Regular database backups

## 🚨 Warnings and Limitations

⚠️ **Important Considerations:**

1. **LLM-Generated Code**: This codebase was generated by AI and may contain unexpected behaviors
2. **Security Risks**: Thorough security review is recommended before production use
3. **Performance Testing**: Extensive testing required for production workloads
4. **Data Integrity**: Always backup important data before processing
5. **Resource Usage**: Monitor memory and CPU usage on large datasets

### Known Limitations
- Large file handling may require memory optimization
- Network-dependent features require stable connections
- Plugin compatibility may vary across versions
- Database performance may degrade with very large datasets

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Guidelines
- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Add appropriate type hints
- Write unit tests for all new code
- Update documentation as needed

### Plugin Development
See `nodupe/core/plugin_system/PLUGIN_DEVELOPMENT_GUIDE.md` for detailed plugin development instructions.

## 📚 Documentation

### API Documentation
- [Plugin Development Guide](nodupe/core/plugin_system/PLUGIN_DEVELOPMENT_GUIDE.md)
- [Graceful Shutdown Standard](nodupe/core/plugin_system/GRACEFUL_SHUTDOWN_STANDARD.md)
- [Performance Improvements](PERFORMANCE_IMPROVEMENTS_SUMMARY.md)

### Additional Resources
- [CI/CD Setup](docs/CI_FIX_SUMMARY.md)
- [Security Review](docs/SECURITY_REVIEW_ARCHIVE_SUPPORT.md)
- [Implementation Plan](implementation_plan.md)

## 🐛 Bug Reports

### Before Reporting
1. Check if the issue exists in the latest version
2. Review existing issues and documentation
3. Try to reproduce the issue consistently

### Reporting Issues
When reporting bugs, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs. actual behavior
- Error messages and stack traces
- Sample code if applicable

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- The Python community for excellent libraries and tools
- Contributors and testers who help improve the project
- The AI systems that generated this codebase

## ⚖️ Disclaimer

This software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.

**Use this software at your own risk. The authors are not responsible for any data loss, security breaches, or other damages resulting from the use of this code.**

---

**⚠️ Reminder**: This is an LLM-generated project. Exercise extreme caution and perform thorough testing and security reviews before using this code in any production environment.
