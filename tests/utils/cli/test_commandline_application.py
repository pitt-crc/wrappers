"""Tests for the ``CommandlineApplication`` class."""

from unittest import TestCase

from apps.utils.cli import CommandlineApplication, Parser


class IsAbstract(TestCase):
    """Test the ``CommandlineApplication`` class is abstract"""

    def test_raises_error(self) -> None:
        """Test an error is raised when instantiating the abstract class"""

        with self.assertRaisesRegex(TypeError, 'abstract class'):
            CommandlineApplication()


class DefaultParser(TestCase):
    """Test the ``app_interface`` method"""

    def test_default_parser(self) -> None:
        """Test a ``Parser`` instance is returned by default"""

        class DummyApp(CommandlineApplication):
            """A dummy application for testing"""

            def app_logic(self, *args) -> None:
                """A placeholder method"""

        self.assertIsInstance(DummyApp().parser, Parser)
