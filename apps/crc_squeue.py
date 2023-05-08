"""A simple wrapper around the Slurm ``squeue`` command."""

import getpass
from argparse import Namespace
from time import sleep

from ._base_parser import BaseParser
from .utils.system_info import Shell


class CrcSqueue(BaseParser):
    """Summarize currently running Slurm jobs."""

    # Formats for output data depending on user provided arguments
    output_format_user = "-o '%.7i %.3P %.35j %.2t %.12M %.6D %.4C %.50R %.20S'"
    output_format_all = "-o '%.7i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.50R %.20S'"

    def __init__(self) -> None:
        """Define the application commandline interface"""

        super(CrcSqueue, self).__init__()
        self.add_argument('-a', '--all', action='store_true', help="show all jobs (defaults to current user only)")
        self.add_argument('-w', '--watch', action='store_const', const=10, help='update information every 10 seconds')
        self.add_argument('-c', '--cluster', nargs='?', help='Only show information for a given cluster name')
        self.add_argument('-z', '--print-command', action='store_true',
                          help='print the equivalent slurm command and exit')

    @classmethod
    def build_slurm_command(cls, args: Namespace) -> str:
        """Return an ``squeue`` command matching parsed command line arguments

        Args:
            args: Parsed command line arguments
        """

        # Build the base command
        command_options = ['squeue -M all']

        if args.all:
            command_options.append(cls.output_format_all)

        else:
            user = f'-u {getpass.getuser()}'
            command_options.append(user)
            command_options.append(cls.output_format_user)

        return ' '.join(command_options)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        command = self.build_slurm_command(args)
        if args.print_command:
            print(command)
            return

        print(Shell.run_command(command))
        while args.watch:
            sleep(args.watch)
            print('\n', Shell.run_command(command))
