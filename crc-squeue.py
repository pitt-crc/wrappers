#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""A simple wrapper around the Slurm ``squeue`` command"""

from os import environ

from _base_parser import BaseParser


class CrcSqueue(BaseParser):
    """Command line application for fetching data from the Slurm ``squeue`` utility"""

    # Formats for output data depending on user provided arguments
    output_user_format = "-o '%.7i %.3P %.35j %.2t %.12M %.6D %.4C %.20R'"
    output_all_format = "-o '%.7i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.20R'"
    output_user_format_start = "-o '%.7i %.3P %.35j %.2t %.12M %.6D %.4C %.20R %.20S'"
    output_all_format_start = "-o '%.7i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.20R %.20S'"

    # Frequency (in seconds) to refresh output when user specifies ``--watch``
    watch_frequency = 10

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcSqueue, self).__init__()
        self.add_argument('-a', '--all', action='store_true', help="show all jobs")
        self.add_argument('-s', '--start', action='store_true', help="add the approximate start time")
        self.add_argument('-w', '--watch', action='store_true', help="updates information every 10 seconds")

    def app_logic(self, args):
        """Logic to evaluate when executing the application

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
            command_options.append(self.output_all_format_start)

        elif args.all:
            command_options.append(self.output_all_format)

        elif args.start:
            command_options.append(self.output_user_format_start)

        else:
            command_options.append(self.output_user_format)

        print(self.run_command(' '.join(command_options)))


if __name__ == '__main__':
    CrcSqueue().execute()
