"""Command line application for displaying Slurm cluster status.

The `crc-sinfo` application wraps the Slurm `sinfo -M all` command and
optionally restricts output to a single cluster.
"""

from argparse import Namespace

from .utils.cli import BaseParser
from .utils.system_info import Shell


class CrcSinfo(BaseParser):
    """Display status information for available Slurm clusters."""

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super().__init__()
        self.add_argument('-c', '--cluster', nargs='?', default='all', help='only show info for the given cluster')
        self.add_argument('-z', '--print-command', action='store_true', help='print the equivalent Slurm command and exit')

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application.

        Args:
            args: Parsed command line arguments.
        """

        command = f'sinfo -M {args.cluster}'
        if args.print_command:
            print(command)

        else:
            print(Shell.run_command(command))
