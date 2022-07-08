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

   from apps.base_parser import BaseParser


   class CrcInteractive(BaseParser):
       \"""This docstring becomes the application description in the CLI help text.\"""

       def __init__(self) -> None:
           \"""Define arguments for the command line interface\"""

           self.add_arguments('-f', '--foo', help="This is help text")

       def app_logic(self, args):
           \"""Logic to evaluate when executing the application

           Args:
               args: Parsed command line arguments
           \"""

           print(args.foo)
"""

__version__ = '0.4.0'
__author__ = 'Pitt Center for Research Computing'
