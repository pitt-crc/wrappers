"""
CRC Wrapper Applications
========================

.. toctree::
   :hidden:

   Overview<self>

.. Source files for documenting individual applications are generated
   dynamically by the sphinx-autoapi plugin. These files are edded below.

.. toctree::
   :hidden:
   :caption: Applications:
   :glob:

   **/*

Custom commandline applications built by the Center for Research Computing.

The wrapper applications provide a simplified interface for running common
HPC tasks on Slurm based clusters. The applications are built specifically for
the CRC and are not designed to work out-of-the-box at other HPC facilities.

Installation
------------

The command line applications are installable as a collective set via the
pip (or pipx) package manager:

.. code-block::

   pipx install git+https://github.com/pitt-crc/wrappers.git

The ``pipx`` utility is recommended for system administrators working in a
multi-tenancy environment.

Contributing a New Application
------------------------------

Wrapper applications are based on the ``argparse`` package from the standard
Python library. The ``BaseParser`` class extends this functionality and
ensures all applications share the same fundamental behavior.

To create a new application, inherit from the ``BaseParser`` class and define
the following:

1. Define the application description as class documentation
2. Define the application arguments (and help text) in the class ``__init__`` method
3. Define the core application logic in the ``app_logic`` method

.. doctest::

   >>> from argparse import Namespace

   >>> from apps._base_parser import BaseParser


   >>> class ExampleApplication(BaseParser):
   ...     \"""This docstring becomes the application description in the CLI help text.\"""
   ...
   ...     def __init__(self) -> None:
   ...         \"""Define arguments for the command line interface\"""
   ...
   ...         super().__init__()
   ...         self.add_argument('-f', '--foo', help="This is help text for foo")
   ...
   ...     def app_logic(self, args: Namespace) -> None:
   ...         \"""Logic to evaluate when executing the application
   ...
   ...         Args:
   ...             args: Parsed command line arguments
   ...         \"""
   ...
   ...         print(args.foo)


You will also need to add the new application to the ``setup.py`` file under
the ``entry_points`` option. The following example assumes the application
class is located in ``apps/example_module.py`` and exposes the application as
an executable called ``executable-name``:

.. code-block::

   >>> from setuptools import setup

   >>> setup(
   ...    entry_points=\"""
   ...        [console_scripts]
   ...        executable-name=apps.example_module:ExampleApplication.execute
   ...    \"""
   ...)

.. note::

   For both clarity and historical reasons, application names are defined
   in files starting with the prefix ``crc_``. Python modules containing
   reusable utilities (and not a dedicated command line app) are named using a
   leading underscore.
"""

__version__ = '0.4.0'
__author__ = 'Pitt Center for Research Computing'
