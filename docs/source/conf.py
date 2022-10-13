"""Configuration file for building application documentation"""

# -- Path setup --------------------------------------------------------------

import sys
from datetime import date

from pathlib import Path

this_dir = Path(__file__).resolve().parent
project_root = this_dir.parent.parent
apps_dir = project_root / 'apps'

# Add the project source code to the working python environment
sys.path.insert(0, str(project_root))

# -- Project information -----------------------------------------------------

from apps import __version__, __author__

project = 'CRC Wrapper Applications'
author = 'Pitt Center for Research Computing'
copyright = f'{date.today().year}, {author}'
release = __version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.doctest',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'autoapi.extension',
    'sphinx_copybutton',
]

# Configure automatic documentation of command line applications
autoapi_type = 'python'
autoapi_dirs = [str(apps_dir)]
autoapi_add_toctree_entry = False
autoapi_template_dir = 'templates'

# Don't include code prompts when copying python code
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['templates']

# The suffix(es) of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
language = 'en'

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
