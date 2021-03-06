"""Tests for the ``crc-squeue`` application."""

from os import environ
from unittest import TestCase

from apps.crc_squeue import CrcSqueue


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_default_flags_are_false(self) -> None:
        """Test default values for all flag arguments are ``False``"""

        app = CrcSqueue()
        args, unknown_args = app.parse_known_args([])
        self.assertFalse(unknown_args)
        self.assertFalse(args.all)
        self.assertFalse(args.start)
        self.assertFalse(args.watch)


class SlurmCommandCreation(TestCase):
    """Test the creation of ``squeue`` commands based on command line arguments"""

    def test_all_option(self) -> None:
        """Test the ``--all`` argument disables ``-u`` in the piped slurm command"""

        app = CrcSqueue()
        slurm_user_argument = "-u {0}".format(environ['USER'])

        # The application should default to showing information for the current user
        args, _ = app.parse_known_args([''])
        slurm_command = app.build_slurm_command(args)
        self.assertIn(slurm_user_argument, slurm_command, '-u flag is missing from slurm command')

        # Make sure user option is disabled when ``--all`` argument is given
        args, _ = app.parse_known_args(['--all'])
        slurm_command = app.build_slurm_command(args)
        self.assertNotIn(slurm_user_argument, slurm_command, '-u flag was added to slurm command')


class OutputFormat(TestCase):
    """Test the correct output format is specified in the piped slurm command"""

    @staticmethod
    def get_slurm_command(cmd_args):
        """Get the slurm command run by the app

        Args:
            cmd_args: Command line arguments to pass to the application

        Returns:
            A shell command as a string
        """

        app = CrcSqueue()
        args, _ = app.parse_known_args(cmd_args)
        return app.build_slurm_command(args)

    def test_defaults_to_user_format(self) -> None:
        """Test the application defaults to using the ``output_format_user`` format"""

        slurm_command = self.get_slurm_command([''])
        self.assertIn(CrcSqueue.output_format_user, slurm_command)

    def test_user_flag(self) -> None:
        """Test the application defaults to using the ``output_format_user`` format"""

        slurm_command = self.get_slurm_command(['--user'])
        self.assertIn(CrcSqueue.output_format_user, slurm_command)

    def test_all_flag(self) -> None:
        """Test the application defaults to using the ``output_format_all`` format"""

        slurm_command = self.get_slurm_command(['--all'])
        self.assertIn(CrcSqueue.output_format_all, slurm_command)

    def test_user_and_start_flag(self) -> None:
        """Test the application defaults to using the ``output_format_user_start`` format"""

        slurm_command = self.get_slurm_command(['--user', '--start'])
        self.assertIn(CrcSqueue.output_format_user_start, slurm_command)

    def test_all_and_start_flags(self) -> None:
        """Test the application defaults to using the ``output_format_all_start`` format"""

        slurm_command = self.get_slurm_command(['--all', '--start'])
        self.assertIn(CrcSqueue.output_format_all_start, slurm_command)
