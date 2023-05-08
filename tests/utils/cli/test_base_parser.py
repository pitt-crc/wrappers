"""Tests for the ``Parser`` class."""

from unittest import TestCase

from apps.utils.cli import BaseParser


class ErrorHandling(TestCase):
    """Test error handling via the ``error`` method"""

    def test_raised_as_system_exit(self) -> None:
        """Test the ``error`` method raises a ``SystemExit`` error

        Ensure error messages are passed to the raised exception.
        """

        message = 'This is a test'
        with self.assertRaisesRegex(SystemExit, message):
            BaseParser().error(message)
