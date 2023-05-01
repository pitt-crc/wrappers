"""Utility classes for building commandline parsers/applications."""

import abc
import logging
import sys
from argparse import ArgumentParser, Namespace, HelpFormatter

from .. import __version__


class Parser(ArgumentParser):
    """Extends the builtin ``ArgumentParser`` class with better formatting and error handling

    Instance are automatically created with a ``--version`` argument.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Define default arguments for the commandline interface"""

        # Increase the default width of the application help text
        formatter_factory = lambda prog: HelpFormatter(prog, max_help_position=50)

        super().__init__(*args, **kwargs, formatter_class=formatter_factory)
        self.add_argument('-v', '--version', action='version', version=f'{self.prog} version {__version__}')

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

        if len(sys.argv) == 1:
            self.print_help()
            raise SystemExit(message)

        raise SystemExit(message)  # pragma: no cover


class CommandlineApplication(metaclass=abc.ABCMeta):
    """Base class for building command line applications.

    Subclasses should define the following:

    1. The commandline interface via the ``app_interface`` method
    2. The top level application logic via the ``app_logic`` method
    """

    def app_interface(self) -> Parser:
        """Define the application commandline interface

        Factory method for creating commandline argument parsers with the
        appropriate interface for the parent application.

        Returns:
            An instantiated commandline parser
        """

        return Parser()

    @abc.abstractmethod
    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

    @classmethod
    def execute(cls) -> None:
        """Parse command line arguments and execute the application"""

        app = cls()
        try:
            args = app.app_interface().parse_args()
            app.app_logic(args)

        except KeyboardInterrupt:
            exit('User interrupt detected - exiting...')

        except Exception as excep:
            logging.error(str(excep))
