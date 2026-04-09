"""Tests for the ``Shell`` utility class."""

from unittest import TestCase

from apps.utils.system_info import Shell


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

class ReturnTypes(TestCase):
    """Test that run_command always returns strings."""

    def test_stdout_only_returns_string(self) -> None:
        out = Shell.run_command('echo hello')
        self.assertIsInstance(out, str)

    def test_with_stderr_returns_two_strings(self) -> None:
        out, err = Shell.run_command('echo hello', include_err=True)
        self.assertIsInstance(out, str)
        self.assertIsInstance(err, str)


# ---------------------------------------------------------------------------
# STDOUT / STDERR capture
# ---------------------------------------------------------------------------

class FileDescriptors(TestCase):
    """Test STDOUT and STDERR are captured and returned correctly."""

    def test_stdout_content_returned(self) -> None:
        out = Shell.run_command("echo 'hello world'")
        self.assertEqual('hello world', out)

    def test_stderr_empty_on_success(self) -> None:
        _, err = Shell.run_command('echo hello', include_err=True)
        self.assertFalse(err)

    def test_stderr_populated_on_error(self) -> None:
        _, err = Shell.run_command('ls /nonexistent_path_xyzzy', include_err=True)
        self.assertTrue(err)

    def test_stdout_empty_on_error(self) -> None:
        out, _ = Shell.run_command('ls /nonexistent_path_xyzzy', include_err=True)
        self.assertFalse(out)

    def test_stdout_stripped_of_trailing_newline(self) -> None:
        """run_command should strip trailing whitespace/newlines from output."""

        out = Shell.run_command('echo hello')
        self.assertFalse(out.endswith('\n'))


# ---------------------------------------------------------------------------
# Multi-line output
# ---------------------------------------------------------------------------

class MultiLineOutput(TestCase):
    """Test that multi-line output is captured correctly."""

    def test_multiline_stdout(self) -> None:
        out = Shell.run_command('printf "line1\\nline2\\nline3"')
        self.assertIn('line1', out)
        self.assertIn('line2', out)
        self.assertIn('line3', out)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class EdgeCases(TestCase):
    """Test edge case behaviours."""

    def test_empty_output_returns_empty_string(self) -> None:
        """A command that produces no output returns an empty string."""

        out = Shell.run_command('true')
        self.assertEqual('', out)

    def test_command_with_special_characters(self) -> None:
        """Commands with special shell characters are handled correctly."""

        out = Shell.run_command("echo 'hello world'")
        self.assertIn('hello', out)
