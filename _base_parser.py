"""Parent classes for building command line applications."""

import abc
import os
import sys
import termios
import tty
from argparse import ArgumentParser
from subprocess import Popen, PIPE


class CommonSettings(object):
    """Parent class for adding common settings to a command line application"""

    banking_db_path = 'sqlite:////ihome/crc/bank/crc_bank.db'
    cluster_partitions = {
        'smp': ['smp', 'high-mem', "legacy"],
        'gpu': ['gtx1080', 'titanx', 'titan', 'k40'],
        'mpi': ['mpi', 'opa', 'ib', "opa-high-mem"],
        'htc': ['htc']
    }


class BaseParser(ArgumentParser):
    """Base class for building command line applications"""

    def __init__(self):
        """Define arguments for the command line interface"""

        super(BaseParser, self).__init__()
        self.add_argument('-v', '--version', action='version', version=self.app_version)

    @staticmethod
    def get_semantic_version():
        """Return the semantic version number of the application"""

        # Look for `version.txt` in the same directory as this file
        file_directory = os.path.dirname(os.path.abspath(__file__))
        version_file = os.path.join(file_directory, 'version.txt')

        with open(version_file) as version_file:
            return version_file.readline().strip()

    @property
    def app_version(self):
        """Return the application name and version as a string"""

        return '{} version {}'.format(self.prog, self.get_semantic_version())

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

        return character

    @abc.abstractmethod
    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        raise NotImplementedError

    @staticmethod
    def run_command(command):
        """Run a command in a dedicated shell

        Args:
            command: The command to execute as a string
        """

        if isinstance(command, str):
            command = command.split()

        process = Popen(command, stdout=PIPE, stderr=PIPE)
        return process.communicate()[0].strip()

    def error(self, message, print_help=True):
        """Print the error message to STDOUT and exit

        Args:
            message: The error message
            print_help: If ``True`` and no arguments were passed, print the help text.
        """

        # If true, then no arguments were provided
        if print_help and len(sys.argv) == 1:
            self.print_help()
            return

        sys.stderr.write('ERROR: {}\n'.format(message))
        sys.exit(2)

    def execute(self):
        """Parse command line arguments and execute the application"""

        try:
            args = self.parse_args()
            self.app_logic(args)

        except KeyboardInterrupt:
            exit('Interrupt detected! exiting...')
