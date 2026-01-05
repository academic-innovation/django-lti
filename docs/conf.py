# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os.path
import sys
from functools import cached_property

import django.conf
import django.utils.functional

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(".."))

# -- Django setup ------------------------------------------------------------

# Sphinx autodoc doesn't recognize functions decorated with @cached_property from
# django.utils.functional as properties, so we swap it here with the one from functools.
# See https://code.djangoproject.com/ticket/30949
django.utils.functional.cached_property = cached_property

django.conf.settings.configure(
    INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "lti_tool"],
    SECRET_KEY="Anyone who finds a URL will be able to log in. Seriously.",
)
django.setup()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "django-lti"
copyright = "2024, Center for Academic Innovation"
author = "Center for Academic Innovation"
release = "0.9.2"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# extensions = []
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = project
html_static_path = ["_static"]
