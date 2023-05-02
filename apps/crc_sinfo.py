"""A simple wrapper around the Slurm ``sinfo`` command.

This application is equivalent to running:

.. code-block:: bash

   sinfo -M all
"""

from argparse import Namespace

from ._base_parser import BaseParser
from .utils.system_info import Shell


class CrcSinfo(BaseParser):
    """Display information about all available Slurm clusters."""

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        print(Shell.run_command("sinfo -M all"))
