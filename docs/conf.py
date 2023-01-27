#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

import django

import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "config.settings.local"
)
django.setup()

from libs.utils import get_latest_version  # noqa

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinxcontrib.blockdiag',
    'recommonmark',
]

# RST support
source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

# Name of master doc
master_doc = 'index'

# General information about the project.
project = 'JusLaw'
copyright = '2020, Saritasa'
author = 'Saritasa'
version = get_latest_version('changelog_backend/changelog.md')
release = get_latest_version('changelog_backend/changelog.md')

language = None

exclude_patterns = []

todo_include_todos = False

# Read the docs theme
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = []

htmlhelp_basename = 'JusLawdoc'

latex_elements = {}

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (
        master_doc,
        'JusLaw',
        'JusLaw Documentation',
        [author],
        1
    )
]

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        'JusLaw',
        'JusLaw Documentation',
        author,
        'JusLaw',
        'One line description of project.',
        'Miscellaneous'
    ),
]
