"""Parent classes used when building command line applications."""

import abc
import os
import sys
from argparse import ArgumentParser, Namespace, HelpFormatter
from textwrap import dedent
from typing import Optional, List

from .. import __version__


class BaseParser(ArgumentParser):
    """Base class for building command line applications.

    Inheriting from this class ensures child applications behave consistently
    and share the same version number.
    """

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        # Increase the default width of the application help text
        formatter_factory = lambda prog: HelpFormatter(prog, max_help_position=50)
        super(BaseParser, self).__init__(formatter_class=formatter_factory)

        # Strip indent from class docs and use as application description
        self.description = '\n'.join(dedent(paragraph) for paragraph in self.__doc__.split('\n'))
        self.add_argument('-v', '--version', action='version', version=self.app_version)

    @property
    def app_version(self) -> str:
        """Return the application name and version as a string"""

        program_name = os.path.splitext(self.prog)[0]
        return '{} version {}'.format(program_name, __version__)

    @abc.abstractmethod
    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        raise NotImplementedError

    def error(self, message: str) -> None:
        """Handle parsing errors and exit the application

        This method mimics the parent class behavior except error messages
        are included in the raised ``SystemExit`` exception. This makes for
        easier testing/debugging.

        If the application was called without any commandline arguments, the
        application help text is printed before exiting.

        Args:
            message: The error message

        Raises:
            SystemExit: Every time the method is run
        """

        # If no commandline arguments were given, print the help text
        if len(sys.argv) == 1:
            self.print_help()

        raise SystemExit(message)

    @classmethod
    def execute(cls, args: Optional[List[str]] = None) -> None:
        """Parse command line arguments and execute the application

        Args:
            args: Optionally parse the given arguments instead of reading STDIN
        """

        app = cls()
        args = app.parse_args(args)

        try:
            app.app_logic(args)

        # Handle interrupt with cleaner error message
        except KeyboardInterrupt:
            exit('User interrupt detected - exiting...')

        except Exception as excep:
            print(str(excep))
