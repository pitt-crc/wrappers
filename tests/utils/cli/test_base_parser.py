"""Tests for the ``Parser`` class."""

import re
from unittest import TestCase

from apps.utils.cli import BaseParser


class DummyApp(BaseParser):
    """A dummy commandline application for use when testing CLI parsing"""

    def app_logic(self, *args) -> None:
        """Placeholder for implementing required methods by the abstract parent class"""


class ParserDescription(TestCase):
    """Test the generation of CLI application descriptions"""

    def test_matches_class_docs(self) -> None:
        """Test CLI descriptions match class documentation

        Whitespace and formatting is ignored.
        """

        app = DummyApp()
        app_description = re.sub(r'\s+', ' ', app.description)
        class_docs = re.sub(r'\s+', ' ', DummyApp.__doc__)
        self.assertEqual(class_docs, app_description)


class ErrorHandling(TestCase):
    """Test error handling via the ``error`` method"""

    def test_raised_as_system_exit(self) -> None:
        """Test the ``error`` method raises a ``SystemExit`` error

        Ensure error messages are passed to the raised exception.
        """

        message = 'This is a test'
        with self.assertRaisesRegex(SystemExit, message):
            DummyApp().error(message)
