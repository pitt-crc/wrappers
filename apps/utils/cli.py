"""Base classes used for building command line applications."""

import abc
import os
import sys
from argparse import ArgumentParser, Namespace, HelpFormatter
from textwrap import dedent
from typing import Optional, List

from .. import __version__


class BaseParser(ArgumentParser, metaclass=abc.ABCMeta):
    """Base class for building commandline applications.

    Child classes should implement the following:

    1. The application commandline interface in the ``__init__`` method
    2. The primary application logic in the ``app_logic`` method

    Unless set explicitly, the application description (``self.description``)
    is pulled from the class docstring.
    """

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        # Increase the default width of the application help text
        formatter_factory = lambda prog: HelpFormatter(prog, max_help_position=50)
        super(BaseParser, self).__init__(formatter_class=formatter_factory)

        # Strip indent from class docs and use as application description
        self.description = '\n'.join(dedent(paragraph) for paragraph in self.__doc__.split('\n'))

        # Set the application version to match the package version
        program_name = os.path.splitext(self.prog)[0]
        version_string = '{} version {}'.format(program_name, __version__)
        self.add_argument('-v', '--version', action='version', version=version_string)

    @abc.abstractmethod
    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

    def error(self, message: str) -> None:
        """Handle errors and exit the application

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
        except KeyboardInterrupt:  # pragma: no cover
            exit('User interrupt detected - exiting...')

        # Route errors to the CLI parser's error handler
        except Exception as excep:  # pragma: no cover
            app.error(str(excep))
