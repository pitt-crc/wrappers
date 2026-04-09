"""Tests for the ``BaseParser`` class."""

import re
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from apps.utils.cli import BaseParser


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------

class DummyApp(BaseParser):
    """A dummy commandline application for use when testing CLI parsing."""

    def app_logic(self, *args) -> None:
        """Placeholder implementing the required abstract method."""


class DummyAppWithArgs(BaseParser):
    """A dummy app that defines its own arguments."""

    def __init__(self) -> None:
        super().__init__()
        self.add_argument('--name', default='world', help='name to greet')
        self.add_argument('--count', type=int, default=1, help='number of times')

    def app_logic(self, *args) -> None:
        pass


# ---------------------------------------------------------------------------
# Description generation
# ---------------------------------------------------------------------------

class ParserDescription(TestCase):
    """Test that the parser description is derived from the class docstring."""

    def test_description_matches_class_docstring(self) -> None:
        """CLI description matches the class docstring (ignoring whitespace)."""

        app = DummyApp()
        app_description = re.sub(r'\s+', ' ', app.description)
        class_docs = re.sub(r'\s+', ' ', DummyApp.__doc__)
        self.assertEqual(class_docs, app_description)

    def test_description_is_a_string(self) -> None:
        self.assertIsInstance(DummyApp().description, str)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class ErrorHandling(TestCase):
    """Test the ``error`` method raises SystemExit with the message."""

    def test_error_raises_system_exit(self) -> None:
        """error() raises SystemExit."""

        with self.assertRaises(SystemExit):
            DummyApp().error('something went wrong')

    def test_error_message_included_in_exception(self) -> None:
        """The error message appears in the SystemExit value."""

        message = 'This is a test error'
        with self.assertRaisesRegex(SystemExit, message):
            DummyApp().error(message)

    def test_different_messages_produce_different_exits(self) -> None:
        """Each distinct message is preserved in its SystemExit."""

        for msg in ('error one', 'error two', 'error three'):
            with self.assertRaisesRegex(SystemExit, msg):
                DummyApp().error(msg)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class ArgumentParsing(TestCase):
    """Test general argument parsing behaviour."""

    def test_defined_arguments_are_parsed(self) -> None:
        """Arguments added in __init__ are accessible on the Namespace."""

        args = DummyAppWithArgs().parse_args(['--name', 'Alice', '--count', '3'])
        self.assertEqual('Alice', args.name)
        self.assertEqual(3, args.count)

    def test_defaults_applied_when_args_omitted(self) -> None:
        """Default values are used when optional arguments are not given."""

        args = DummyAppWithArgs().parse_args([])
        self.assertEqual('world', args.name)
        self.assertEqual(1, args.count)

    def test_unknown_args_returned_by_parse_known_args(self) -> None:
        """Unknown arguments are returned as leftovers by parse_known_args."""

        _, unknown = DummyAppWithArgs().parse_known_args(['--unknown-flag'])
        self.assertIn('--unknown-flag', unknown)

    def test_parse_args_exits_on_unknown_args(self) -> None:
        """parse_args raises SystemExit when unknown arguments are given."""

        with self.assertRaises(SystemExit):
            DummyAppWithArgs().parse_args(['--totally-unknown'])


# ---------------------------------------------------------------------------
# execute / app_logic integration
# ---------------------------------------------------------------------------

class ExecuteMethod(TestCase):
    """Test that execute() calls app_logic with parsed arguments."""

    def test_execute_calls_app_logic(self) -> None:
        """execute() invokes app_logic exactly once."""

        call_log = []

        class TrackingApp(BaseParser):
            """Tracking app."""
            def app_logic(self, args):
                call_log.append(args)

        TrackingApp().execute([])
        self.assertEqual(1, len(call_log))

    def test_execute_passes_parsed_namespace(self) -> None:
        """app_logic receives a Namespace with correctly parsed values."""

        received = []

        class TrackingApp(BaseParser):
            """Tracking app."""
            def __init__(self):
                super().__init__()
                self.add_argument('--value', default='default')

            def app_logic(self, args):
                received.append(args)

        TrackingApp().execute(['--value', 'custom'])
        self.assertEqual('custom', received[0].value)
