"""Tests for the ``Parser`` class."""

from unittest import TestCase, mock

from apps.utils.cli import Parser


class ErrorHandling(TestCase):
    """Test error handling via the ``error`` method"""

    def test_raised_as_system_exit(self) -> None:
        """Test the ``error`` method raises a ``SystemExit`` error

        Ensure error messages are passed to the raised exception.
        """

        message = 'This is a test'
        with self.assertRaisesRegex(SystemExit, message):
            Parser().error(message)

    @mock.patch('argparse.ArgumentParser.print_help')
    def test_help_is_printed(self, mock_print_help: mock.Mock) -> None:
        """Test help text is printed when running without commandline arguments"""

        with self.assertRaises(SystemExit):
            Parser().error('this is a test')

        mock_print_help.assert_called()
