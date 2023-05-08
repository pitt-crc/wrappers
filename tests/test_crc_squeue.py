"""Tests for the ``crc-squeue`` application."""

import getpass
from unittest import TestCase

from apps.crc_squeue import CrcSqueue


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_default_arguments_are_false(self) -> None:
        """Test default values for all flag arguments are ``False``"""

        app = CrcSqueue()
        args = app.parse_args([])
        self.assertFalse(args.all)
        self.assertFalse(args.watch)
        self.assertFalse(args.print_command)

    def test_defaults_to_all_clusters(self) -> None:
        """Test the cluster argument defaults to ``all`` clusters"""

        app = CrcSqueue()
        args = app.parse_known_args([])
        self.assertEqual('all', args.cluster)

    def test_custom_clusters(self) -> None:
        """Test the custom cluster names are stored by the parser"""

        app = CrcSqueue()
        args = app.parse_args(['-c', 'smp'])
        self.assertEqual('smp', args.cluster)

        args = app.parse_args(['--cluster', 'smp'])
        self.assertEqual('smp', args.cluster)

    def watch_argument_stores_const(self) -> None:
        """Test the ``--watch`` argument stores the update interval as an integer"""

        app = CrcSqueue()
        args = app.parse_args(['--w'])
        self.assertEqual(10, args.watch)

        args = app.parse_args(['--watch'])
        self.assertEqual(10, args.watch)


class SlurmCommandCreation(TestCase):
    """Test the creation of ``squeue`` commands based on command line arguments"""

    def test_user_option(self) -> None:
        """Test the ``--all`` argument toggles the slurm ``-u`` option in the returned command"""

        app = CrcSqueue()
        slurm_user_argument = f'-u {getpass.getuser()}'

        # The application should default to showing information for the current user
        args = app.parse_args([])
        slurm_command = app.build_slurm_command(args)
        self.assertIn(slurm_user_argument, slurm_command, '-u flag is missing from slurm command')

        # Make sure user option is disabled when ``--all`` argument is given
        args = app.parse_args(['--all'])
        slurm_command = app.build_slurm_command(args)
        self.assertNotIn(slurm_user_argument, slurm_command, '-u flag was added to slurm command')

    def test_cluster_name(self) -> None:
        """Test the generated slurm command specifies the correct cluster"""

        app = CrcSqueue()

        args = app.parse_args([])
        slurm_command = app.build_slurm_command(args)
        self.assertIn('-M all', slurm_command)

        args = app.parse_args(['-c', 'smp'])
        slurm_command = app.build_slurm_command(args)
        self.assertIn('-M smp', slurm_command)


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

    def test_all_flag(self) -> None:
        """Test the application defaults to using the ``output_format_all`` format"""

        slurm_command = self.get_slurm_command(['--all'])
        self.assertIn(CrcSqueue.output_format_all, slurm_command)
