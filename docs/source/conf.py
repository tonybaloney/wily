"""Sphinx configuration for wily documentation."""

import os.path
import sys

sys.path.insert(0, os.path.abspath("../"))

# -- Project information -----------------------------------------------------

project = "wily"
copyright = "2018, Anthony Shaw"
author = "Anthony Shaw"

try:
    import wily

    version = wily.__version__
except ImportError:
    version = "dev"

release = version

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx_click",
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
language = "en"
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = "alabaster"

html_theme_options = {
    "logo": "logo_below.png",
    "logo_name": False,
    "logo_text_align": "center",
    "github_user": "tonybaloney",
    "github_repo": "wily",
    "github_banner": True,
    "github_button": False,
    "fixed_sidebar": True,
    "extra_nav_links": {
        "wily@PyPi": "https://pypi.python.org/pypi/wily/",
        "wily@github": "https://github.com/tonybaloney/wily",
    },
}

html_static_path = ["_static"]

html_sidebars = {
    "**": ["about.html", "navigation.html", "searchbox.html"],
}

htmlhelp_basename = "wilydoc"

# -- Options for todo extension ----------------------------------------------

todo_include_todos = True
