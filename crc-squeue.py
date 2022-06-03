#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""A simple wrapper around the Slurm squeue command"""

from os import system, environ

from _base_parser import BaseParser


class CrcSqueue(BaseParser):
    """Command line application for fetching data from the Slurm ``squeue`` utility"""

    # Formats for output data depending on user provided arguments
    output_user_format = "-o '%.7i %.3P %.35j %.2t %.12M %.6D %.4C %.20R'"
    output_all_format = "-o '%.7i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.20R'"
    output_user_format_start = "-o '%.7i %.3P %.35j %.2t %.12M %.6D %.4C %.20R %.20S'"
    output_all_format_start = "-o '%.7i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.20R %.20S'"

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcSqueue, self).__init__()
        self.add_argument('-a', '--all', action='store true', help="show all jobs")
        self.add_argument('-s', '--start', action='store true', help="add the approximate start time")
        self.add_argument('-w', '--watch', action='store true', help="updates information every 10 seconds")

    def app_logic(self, args):

        # Useful variables for building shell commands
        user = "-u {0}".format(environ['USER'])
        squeue = "squeue -M all"
        watch = "-i 10"

        if args.all and args.start and args.watch:
            command = "{0} {1} {2}".format(squeue, watch, self.output_all_format_start)

        elif args.all and args.start:
            command = "{0} {1}".format(squeue, self.output_all_format_start)

        elif args.all and args.watch:
            command = "{0} {1} {2}".format(squeue, watch, self.output_all_format)

        elif args.start and args.watch:
            command = "{0} {1} {2} {3}".format(squeue, user, watch, self.output_user_format_start)

        elif args.all:
            command = "{0} {1}".format(squeue, self.output_all_format)

        elif args.start:
            command = "{0} {1} {2}".format(squeue, user, self.output_user_format_start)

        elif args.watch:
            command = "{0} {1} {2} {3}".format(squeue, user, watch, self.output_user_format)

        else:
            command = "{0} {1} {2}".format(squeue, user, self.output_user_format)

        system(command)


if __name__ == '__main__':
    CrcSqueue().execute()
