"""Tests for the ``BaseParser`` class."""

from unittest import TestCase, mock, skip

from apps.utils.cli import Parser


class ErrorHandling(TestCase):
    """Test error handling via the ``error`` method"""

    def test_raised_as_system_exit(self) -> None:
        """Test the ``error`` method raises a ``SystemExit`` error"""

        message = 'This is a test'
        with self.assertRaisesRegex(SystemExit, message):
            Parser().error(message)

    @skip
    @mock.patch('apps.utils.cli.Parser.print_help')
    def test_help_is_printed(self, mock_print_help: mock.Mock) -> None:
        """Test help text is printed automatically by default"""

        with self.assertRaises(SystemExit):
            Parser().error('this is a test')

        mock_print_help.assert_called()
