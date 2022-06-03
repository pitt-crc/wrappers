import sys
from argparse import ArgumentParser


class BaseParser(ArgumentParser):

    def __init__(self):
        """Define arguments for the command line interface"""

        super(BaseParser, self).__init__()
        self.add_argument('-v', '--version', action='version', version=self.app_version)

    @property
    def app_version(self):
        """Return the application name and version as a string"""

        with open('version.txt') as version_file:
            version = version_file.readline().strip()

        return '{} version {}'.format(self.prog, version)

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
