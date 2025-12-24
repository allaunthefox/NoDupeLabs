# NoDupeLabs Documentation

This directory contains the documentation source files for NoDupeLabs, built using both Sphinx and MkDocs for maximum flexibility and quality.

## 📚 Documentation Systems

### 🎯 **Triple-System Architecture (Optimized for Accessibility & Flexibility)**

We use **three complementary documentation systems** to provide maximum accessibility and flexibility for all users:

#### MkDocs (Primary Web Documentation)
- **Live Site**: [nodupelabs.readthedocs.io](https://nodupelabs.readthedocs.io)
- **Theme**: Material for MkDocs
- **Features**: Modern design, search, dark mode, mobile-friendly
- **Accessibility**: WCAG 2.1 AA compliant, keyboard navigation, screen reader support

#### Sphinx (API Documentation)
- **Purpose**: Comprehensive API documentation and technical reference
- **Theme**: Read the Docs
- **Features**: Automatic API docs, cross-references, PDF generation
- **Accessibility**: Semantic HTML, navigation, search functionality

#### Markify (Multi-Format Publishing)
- **Purpose**: Convert documentation to multiple accessible formats
- **Output Formats**: HTML, PDF, EPUB
- **Features**: Advanced Markdown processing, image optimization, template system
- **Accessibility**: PDF accessibility (tags, bookmarks), EPUB accessibility (reflowable text), multiple output formats

### ♿ **Why Three Systems? (Accessibility & Flexibility Benefits)**

**Multiple Formats for Different Needs:**
- **HTML (Web)**: Screen readers, keyboard navigation, real-time updates
- **PDF (Print)**: Offline reading, assistive technology support, print accessibility
- **EPUB (E-reader)**: Text-to-speech compatibility, reflowable text, mobile access

**Universal Access:**
- ✅ **Visual Impairments**: Screen readers work with HTML, PDF, and EPUB
- ✅ **Motor Disabilities**: Keyboard navigation across all formats
- ✅ **Learning Disabilities**: Multiple formats accommodate different learning styles
- ✅ **Offline Access**: PDF/EPUB for users without reliable internet
- ✅ **Device Compatibility**: Web, mobile, e-readers, print
- ✅ **User Choice**: Different users can choose their preferred format

**Maximum Flexibility:**
- **Content Types**: User guides (MkDocs), API docs (Sphinx), multi-format (Markify)
- **Distribution**: Web, print, digital, offline
- **Use Cases**: Online reference, offline study, print documentation
- **Future-Proof**: Multiple systems ensure continued accessibility as technology evolves

## 🚀 Quick Start

### Building Documentation Locally

```bash
# Build both Sphinx and MkDocs documentation
python scripts/build_docs.py

# Build only MkDocs (faster)
python scripts/build_docs.py --builder mkdocs

# Build only Sphinx
python scripts/build_docs.py --builder sphinx

# Clean and rebuild
python scripts/build_docs.py --clean
```

### Viewing Documentation

```bash
# MkDocs (served locally)
cd site && python -m http.server 8000
# Then visit: http://localhost:8000

# Or use MkDocs serve (requires mkdocs installed)
mkdocs serve
# Then visit: http://127.0.0.1:8000
```

## 📁 Documentation Structure

```
docs/
├── source/                 # Sphinx source files
│   ├── conf.py            # Sphinx configuration
│   └── api/               # API documentation
├── getting-started/       # Installation and setup guides
├── user-guide/           # Usage instructions and tutorials
├── development/          # Contributing and development docs
├── resources/            # FAQ, troubleshooting, changelog
├── api/                  # API reference (auto-generated)
└── index.md             # Main documentation index
```

## 🛠️ Documentation Development

### Writing Documentation

1. **Markdown Format**: All documentation is written in Markdown
2. **Front Matter**: Add YAML front matter for MkDocs metadata:
   ```markdown
   ---
   title: Page Title
   ---
   ```

3. **Cross-References**: Use MkDocs linking for internal links:
   ```markdown
   [Link to page](getting-started/installation.md)
   ```

### API Documentation

API documentation is automatically generated from Python docstrings:

```python
def example_function(param: str) -> bool:
    """
    Brief description of the function.
    
    Args:
        param: Description of the parameter
        
    Returns:
        Description of the return value
        
    Example:
        ```python
        result = example_function("test")
        ```
    """
    return True
```

### Adding New Pages

1. Create a new `.md` file in the appropriate directory
2. Add it to the navigation in `mkdocs.yml`
3. For Sphinx, ensure it's included in `docs/source/conf.py`

## 🤖 Automatic Documentation

### CI/CD Integration

Documentation is automatically built and deployed via GitHub Actions:

- **Push to main/master**: Automatically deploys to GitHub Pages
- **Pull Requests**: Creates preview artifacts
- **Tags**: Triggers full deployment with PyPI release

### Build Artifacts

- **Sphinx**: `docs/_build/` directory
- **MkDocs**: `site/` directory
- **GitHub Pages**: `gh-pages` branch

## 🎨 Styling and Themes

### MkDocs Material Theme

Features:
- ✅ Dark/Light mode toggle
- ✅ Search functionality
- ✅ Mobile responsive
- ✅ Navigation tabs
- ✅ Code highlighting
- ✅ Admonitions (notes, warnings, tips)

### Custom Styling

- **CSS**: `docs/stylesheets/extra.css`
- **JavaScript**: `docs/javascripts/extra.js`
- **Icons**: Font Awesome integration

## 🔗 External Links

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Guide](https://www.sphinx-doc.org/en/master/usage/restructuredtext/)

## 🐛 Troubleshooting

### Common Issues

1. **Missing dependencies**:
   ```bash
   pip install -e .[docs]  # For Sphinx
   pip install -e .[mkdocs]  # For MkDocs
   ```

2. **Build errors**:
   ```bash
   python scripts/build_docs.py --clean  # Clean build
   ```

3. **Import errors in API docs**:
   - Ensure all dependencies are installed
   - Check Python path configuration in `docs/source/conf.py`

### Getting Help

- Check the [FAQ](resources/faq.md)
- Review [troubleshooting guide](resources/troubleshooting.md)
- Create an [issue](https://github.com/allaunthefox/NoDupeLabs/issues)

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes to documentation
4. Test locally with `python scripts/build_docs.py`
5. Submit a pull request

### Documentation Standards

- ✅ Write in clear, concise English
- ✅ Use examples and code snippets
- ✅ Include cross-references where helpful
- ✅ Test all code examples
- ✅ Update navigation when adding pages
- ✅ Follow the established style guide

---

## 📋 **Documentation System Choice Rationale**

### **Why Three Systems?**

After careful consideration, we chose to implement **all three documentation systems** (MkDocs, Sphinx, and Markify) to provide **maximum flexibility and accessibility** for our users.

### **Accessibility-First Decision**

This choice was made specifically to ensure our documentation is accessible to the widest possible audience:

- **Multiple Formats**: HTML (web), PDF (print), EPUB (e-reader)
- **Universal Access**: Screen readers, keyboard navigation, offline access
- **Device Compatibility**: Web, mobile, e-readers, print
- **User Choice**: Different users can choose their preferred format
- **Learning Styles**: Accommodates different learning preferences

### **Flexibility Benefits**

- **Content Types**: User guides (MkDocs), API docs (Sphinx), multi-format (Markify)
- **Distribution**: Web, print, digital, offline
- **Use Cases**: Online reference, offline study, print documentation
- **Future-Proof**: Multiple systems ensure continued accessibility as technology evolves

### **Trade-offs Considered**

While maintaining three systems adds complexity, the **accessibility and flexibility benefits** outweigh the maintenance overhead. This approach ensures our documentation remains accessible to users with diverse needs and preferences.

**Note**: This documentation system is automatically updated when code changes. Keep docstrings up-to-date for the best API documentation!
