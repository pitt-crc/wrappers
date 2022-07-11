"""Tests for the ``Shell`` class"""

from unittest import TestCase

from apps.system_info import Shell


class FileDescriptors(TestCase):
    """Test STDOUT and STDERR are captured and returned"""

    def test_capture_on_success(self) -> None:
        """Test for command writing to STDOUT"""

        test_message = 'hello world'
        out, err = Shell.run_command(f"echo '{test_message}'", include_err=True)
        self.assertEqual(test_message, out)
        self.assertFalse(err)

    def test_capture_on_err(self) -> None:
        """Test for command writing to STDERR"""

        out, err = Shell.run_command("ls fake_dr", include_err=True)
        self.assertFalse(out)
        self.assertTrue(err)


class ReturnIsDecoded(TestCase):
    """Test return values are decoded into strings"""

    def test_stdout_only(self):
        """Test returns when ``include_err`` is ``False``"""

        out = Shell.run_command('echo hello world')
        self.assertIsInstance(out, str)

    def test_with_stderr(self):
        """Test returns when ``include_err`` is ``True``"""

        out, err = Shell.run_command('echo hello world', include_err=True)
        self.assertIsInstance(out, str)
        self.assertIsInstance(err, str)
