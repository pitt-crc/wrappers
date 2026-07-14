"""Command line application for summarizing running Slurm jobs.

The `crc-squeue` application wraps the Slurm `squeue` command with
opinionated output formatting. By default it shows only the current user's
jobs, with an option to show all jobs across the cluster.
"""

import getpass
from argparse import Namespace
from time import sleep

from .utils.cli import BaseParser
from .utils.system_info import Shell


class CrcSqueue(BaseParser):
    """Display currently running Slurm jobs."""

    # Formats for output data depending on user provided arguments
    output_format_user = "-o '%.8i %.3P %.35j %.2t %.12M %.6D %.4C %.50R %.20S'"
    output_format_all = "-o '%.8i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.50R %.20S'"

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super(CrcSqueue, self).__init__()
        self.add_argument('-a', '--all', action='store_true', help='show jobs for all users')
        self.add_argument('-c', '--cluster', nargs='?', default='all', help='only show jobs for the given cluster')
        self.add_argument('-w', '--watch', action='store_const', const=10, help='refresh output every 10 seconds')
        self.add_argument('-z', '--print-command', action='store_true', help='print the equivalent Slurm command and exit')

    @classmethod
    def build_slurm_command(cls, args: Namespace) -> str:
        """Return an `squeue` command string matching the parsed arguments.

        Args:
            args: Parsed command line arguments.

        Returns:
            A complete `squeue` command string.
        """

        parts = [f'squeue -M {args.cluster}']

        if args.all:
            parts.append(cls.output_format_all)

        else:
            parts.append(f'-u {getpass.getuser()}')
            parts.append(cls.output_format_user)

        return ' '.join(parts)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application.

        Args:
            args: Parsed command line arguments.
        """

        command = self.build_slurm_command(args)
        if args.print_command:
            print(command)
            return

        print(Shell.run_command(command))
        while args.watch:
            sleep(args.watch)
            print('\n', Shell.run_command(command))
