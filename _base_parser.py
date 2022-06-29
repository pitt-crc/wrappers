"""Parent classes for building command line applications."""

import abc
import os
import sys
import termios
import tty
from argparse import ArgumentParser, HelpFormatter
from shlex import split
from subprocess import Popen, PIPE


class CommonSettings(object):
    """Parent class for adding common settings to a command line application"""

    banking_db_path = 'sqlite:////ihome/crc/bank/crc_bank.db'
    cluster_names = ('smp', 'gpu', 'mpi', 'htc')


class BaseParser(ArgumentParser):
    """Base class for building command line applications"""

    # Maximum starting point of help text argument descriptions
    help_width = 50

    def __init__(self):
        """Define arguments for the command line interface"""

        super(BaseParser, self).__init__()
        self.add_argument('-v', '--version', action='version', version=self.app_version)

    def _get_formatter(self):
        return HelpFormatter(self.prog, max_help_position=self.help_width)

    @property
    def app_version(self):
        """Return the application name and version as a string"""

        # Look for `version.txt` in the same directory as this file
        file_directory = os.path.dirname(os.path.abspath(__file__))
        version_file = os.path.join(file_directory, 'version.txt')

        with open(version_file) as version_file:
            semantic_version = version_file.readline().strip()

        program_name = os.path.splitext(self.prog)[0]
        return '{} version {}'.format(program_name, semantic_version)

    @staticmethod
    def readchar():
        """Read a character from the command line"""

        # Get the current settings of the standard input file descriptor
        file_descriptor = sys.stdin.fileno()
        old_settings = termios.tcgetattr(file_descriptor)

        try:
            tty.setraw(sys.stdin.fileno())
            character = sys.stdin.read(1)

        finally:
            # Restore the original standard input settings
            termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)

        print('')
        return character

    @abc.abstractmethod
    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        raise NotImplementedError

    @staticmethod
    def run_command(command, include_err=False):
        """Run a command in a dedicated shell

        Args:
            command: The command to execute as a string
            include_err: Include output to stderr in the returned values

        Returns:
            The output to stdout and (optionally) stderr
        """

        command_list = split(command)
        process = Popen(command_list, stdout=PIPE, stderr=PIPE, shell=False)
        std_out, std_err = process.communicate()
        if include_err:
            return std_out.strip(), std_err.strip()

        return std_out.strip()

    def error(self, message):
        """Print the error message to STDOUT and exit

        Args:
            message: The error message
        """

        # If true, then no arguments were provided
        if len(sys.argv) == 1:
            self.print_help()
            self.exit()

        sys.stderr.write('ERROR: {}\n'.format(message))
        sys.exit(2)

    def execute(self):
        """Parse command line arguments and execute the application"""

        try:
            args = self.parse_args()
            self.app_logic(args)

        except KeyboardInterrupt:
            exit('Interrupt detected! exiting...')
