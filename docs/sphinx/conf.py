import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

project = 'NoDupeLabs'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']
templates_path = ['_templates']
exclude_patterns = ['_build', 'venv']
html_theme = 'alabaster'

autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
