#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""A simple wrapper around the Slurm ``squeue`` command"""

from os import environ

from _base_parser import BaseParser
from _utils import Shell


class CrcSqueue(BaseParser):
    """Command line application for fetching data from the Slurm ``squeue`` utility"""

    # Formats for output data depending on user provided arguments
    output_format_user = "-o '%.7i %.3P %.35j %.2t %.12M %.6D %.4C %.20R'"
    output_format_all = "-o '%.7i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.20R'"
    output_format_user_start = "-o '%.7i %.3P %.35j %.2t %.12M %.6D %.4C %.20R %.20S'"
    output_format_all_start = "-o '%.7i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.20R %.20S'"

    # Frequency (in seconds) to refresh output when user specifies ``--watch``
    watch_frequency = 10

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcSqueue, self).__init__()
        self.add_argument('-a', '--all', action='store_true', help="show all jobs")
        self.add_argument('-s', '--start', action='store_true', help="add the approximate start time")
        self.add_argument('-w', '--watch', action='store_true', help="updates information every 10 seconds")

    def build_slurm_command(self, args):
        """Return an ``squeue`` command matching parsed command line arguments

        Args:
            args: Parsed command line arguments
        """

        # Variables for building shell commands
        user = "-u {0}".format(environ['USER'])
        watch = "-i {0}".format(self.watch_frequency)

        # Build the base command
        command_options = ["squeue -M all"]
        if not args.all:
            command_options.append(user)

        if args.watch:
            command_options.append(watch)

        # Add on the necessary output format
        if args.all and args.start:
            command_options.append(self.output_format_all_start)

        elif args.all:
            command_options.append(self.output_format_all)

        elif args.start:
            command_options.append(self.output_format_user_start)

        else:
            command_options.append(self.output_format_user)

        return ' '.join(command_options)

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        command = self.build_slurm_command(args)
        print(Shell.run_command(command))


if __name__ == '__main__':
    CrcSqueue().execute()
