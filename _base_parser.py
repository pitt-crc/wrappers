"""Parent classes for building command line applications."""

import abc
import sys
from argparse import ArgumentParser
from subprocess import Popen, PIPE


class BaseParser(ArgumentParser):
    """Base class for building command line applications"""

    def __init__(self):
        """Define arguments for the command line interface"""

        super(BaseParser, self).__init__()
        self.add_argument('-v', '--version', action='version', version=self.app_version)

    @staticmethod
    def get_semantic_version():
        """Return the semantic version number of the application"""

        with open('version.txt') as version_file:
            return version_file.readline().strip()

    @property
    def app_version(self):
        """Return the application name and version as a string"""

        return '{} version {}'.format(self.prog, self.get_semantic_version())

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

        process = Popen(command, stdout=PIPE)
        return process.communicate()

    def error(self, message):
        """Print the error message to STDOUT and exit

        If the application was called without any arguments, print the help text.

        Args:
            message: The error message
        """

        if len(sys.argv) == 1:
            self.print_help()

        else:
            sys.stderr.write('ERROR: {}\n'.format(message))

        sys.exit(2)

    def execute(self):
        """Parse command line arguments and execute the application"""

        args = self.parse_args()
        try:
            self.app_logic(args)

        except KeyboardInterrupt:
            exit('Interrupt detected! exiting...')
