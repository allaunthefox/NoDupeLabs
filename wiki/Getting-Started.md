# Getting Started

## Installation

```bash
# Clone the repository
git clone https://github.com/allaunthefox/NoDupeLabs.git
cd NoDupeLabs

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .
```

## Basic Usage

### Scan for Duplicates

```bash
nodupe scan /path/to/directory
```

### Apply Changes

```bash
nodupe apply --plan plan.json
```

### Check Similarity

```bash
nodupe similarity --file document.txt
```

## Configuration

Create `nodupe.toml` in your project root:

```toml
[database]
path = ".nodupe/database.db"

[scanning]
threads = 4
hash_size = 8192
```

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
nodupe/
├── core/           # Core system modules
├── plugins/        # Plugin implementations
└── ...
```

## Next Steps

- Read the [Architecture Overview](Architecture/Overview.md)
- Learn about [Plugin Development](Development/Plugins.md)
- Check the [CLI Reference](API/CLI.md)
