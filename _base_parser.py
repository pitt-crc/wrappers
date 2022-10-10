"""Parent classes for building command line applications."""

import abc
import os
import sys
from argparse import ArgumentParser, HelpFormatter


class BaseParser(ArgumentParser):
    """Base class for building command line applications"""

    # Maximum starting point of help text argument descriptions
    help_width = 50

    def __init__(self):
        """Define arguments for the command line interface"""

        super(BaseParser, self).__init__()
        self.add_argument('-v', '--version', action='version', version=self.app_version)

    def _get_formatter(self):
        """Returns a ``HelpFormatter`` object for formatting application help text"""

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

    @abc.abstractmethod
    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        raise NotImplementedError

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

        new_app_name = self.prog.replace('.py', '')
        print(f'{self.prog} is being deprecated. Please use {new_app_name} instead.')

        try:
            args = self.parse_args()
            self.app_logic(args)

        except KeyboardInterrupt:
            exit('Interrupt detected! exiting...')
