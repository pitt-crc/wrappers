import sys
from argparse import ArgumentParser

from _version import __version__


class BaseParser(ArgumentParser):

    def __init__(self):
        super(BaseParser, self).__init__()
        self.add_argument('-v', '--version', action='version', version=self.app_version)

    @property
    def app_version(self):
        return '{} version {}'.format(self.prog, __version__)

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
