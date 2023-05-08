"""A simple wrapper around the Slurm ``sinfo`` command.

This application is equivalent to running:

.. code-block:: bash

   sinfo -M all
"""

from argparse import Namespace

from .utils.cli import BaseParser
from .utils.system_info import Shell


class CrcSinfo(BaseParser):
    """Display information about available Slurm clusters."""

    def __init__(self) -> None:
        """Define the application commandline interface"""

        super().__init__()
        self.add_argument('-c', '--cluster', nargs='?', default='all', help='only show jobs for the given cluster')
        self.add_argument(
            '-z', '--print-command', action='store_true',
            help='print the equivalent slurm command and exit')

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        command = f'sinfo -M {args.cluster}'
        if args.print_command:
            print(command)

        else:
            print(Shell.run_command(command))
