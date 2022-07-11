"""Parent classes for building command line applications."""

import abc
import os
import sys
from argparse import ArgumentParser, HelpFormatter

from . import __version__


class BaseParser(ArgumentParser):
    """Base class for building command line applications"""

    # Maximum starting point of help text argument descriptions
    help_width = 50

    def __init__(self):
        """Define arguments for the command line interface"""

        super(BaseParser, self).__init__()
        self.description = self.__doc__

        self.add_argument('-v', '--version', action='version', version=self.app_version)

    def _get_formatter(self):
        """Returns a ``HelpFormatter`` object for formatting application help text"""

        return HelpFormatter(self.prog, max_help_position=self.help_width)

    @property
    def app_version(self):
        """Return the application name and version as a string"""

        program_name = os.path.splitext(self.prog)[0]
        return '{} version {}'.format(program_name, __version__)

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

    @classmethod
    def execute(cls):
        """Parse command line arguments and execute the application"""

        app = cls()
        try:
            args = app.parse_args()
            app.app_logic(args)

        except KeyboardInterrupt:
            exit('Interrupt detected! Exiting...')
