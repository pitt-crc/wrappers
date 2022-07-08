"""Custom commandline applications built by the Center for Research Computing.

The wrapper applications provide a simplified interface from running common
tasks on Slurm based HPC clusters. The applications are built specifically for
the CRC. Some applications may work out-of-the-box at other HPC facilities,
but others may require some modification.

Installation
------------

The command line applications are installable via the pip (or pipx) package
manager:

.. code-block::

   pip install git+https://github.com/pitt-crc/wrappers.git

Contributing a New Application
------------------------------

Command line applications are based on the ``argparse`` from the standard
Python library. To create a new application, inherit from the ``BaseParser``
class and define the following:

1. Define the application description as class documentation
2. Define the application arguments (and help text) in the class ``__init__`` method
3. Define the core application logic in the ``app_logic`` method

.. code-block::

   from argparse import Namespace

   from apps.base_parser import BaseParser


   class ExampleApplication(BaseParser):
       \"""This docstring becomes the application description in the CLI help text.\"""

       def __init__(self) -> None:
           \"""Define arguments for the command line interface\"""

           self.add_arguments('-f', '--foo', help="This is help text")

       def app_logic(self, args: Namespace) -> None:
           \"""Logic to evaluate when executing the application

           Args:
               args: Parsed command line arguments
           \"""

           print(args.foo)


You will also need to add the new application to the ``setup.py`` file under
the ``entry_points`` option. The following example assumes the application
class is located in ``apps/example_module.py`` and exposes the application as
an executable called ``executable-name``:

.. code-block::
   setup(
       entry_points=\"""
           [console_scripts]
           executable-name=apps.example_module:ExampleApplication.execute
       \"""
"""

__version__ = '0.4.0'
__author__ = 'Pitt Center for Research Computing'
