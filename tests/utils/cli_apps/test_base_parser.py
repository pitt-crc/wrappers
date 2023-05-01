"""Tests for the ``BaseParser`` class."""

from unittest import TestCase, mock

from apps.utils.cli_apps import Parser


class ApplicationVersion(TestCase):
    """Test the commandline version argument"""

    def test_has_version_argument(self) -> None:
        """Test instances have a ``version`` argument by default"""

        args, unknown_args = Parser().parse_known_args(['--version'])
        self.assertFalse(unknown_args)


class ErrorHandling(TestCase):
    """Test error handling via the ``error`` method"""

    def test_raised_as_system_exit(self) -> None:
        """Test the ``error`` method raises a ``SystemExit`` error"""

        message = 'This is a test'
        with self.assertRaisesRegex(SystemExit, message):
            Parser().error(message)

    @mock.patch('apps.utils.parsing.BaseParser.print_help')
    def test_help_is_printed(self, mock_print_help: mock.Mock):
        """Test help text is printed automatically by default"""

        message = 'This is a test'
        with self.assertRaisesRegex(SystemExit, message):
            Parser().error(message)

        mock_print_help.assert_called()
