"""Tests for the ``crc-squeue`` application."""

import getpass
from io import StringIO
from unittest import TestCase
from unittest.mock import patch, Mock

from apps.crc_squeue import CrcSqueue


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_default_arguments_are_false(self) -> None:
        """Test default values for all flag arguments are ``False``"""

        app = CrcSqueue()
        args, _ = app.parse_known_args([])
        self.assertFalse(args.all)
        self.assertFalse(args.watch)
        self.assertFalse(args.print_command)

    def test_defaults_to_all_clusters(self) -> None:
        """Test the cluster argument defaults to ``all`` clusters"""

        app = CrcSqueue()
        args, _ = app.parse_known_args([])
        self.assertEqual('all', args.cluster)

    def test_custom_clusters(self) -> None:
        """Test the custom cluster names are stored by the parser"""

        app = CrcSqueue()
        args, _ = app.parse_known_args(['-c', 'smp'])
        self.assertEqual('smp', args.cluster)

        args, _ = app.parse_known_args(['--cluster', 'smp'])
        self.assertEqual('smp', args.cluster)

    def test_watch_argument_stores_const(self) -> None:
        """Test the ``--watch`` argument stores the update interval as an integer"""

        app = CrcSqueue()
        args, _ = app.parse_known_args(['--w'])
        self.assertEqual(10, args.watch)

        args, _ = app.parse_known_args(['--watch'])
        self.assertEqual(10, args.watch)


class SlurmCommandCreation(TestCase):
    """Test the creation of ``squeue`` commands based on command line arguments"""

    def test_user_option(self) -> None:
        """Test the ``--all`` argument toggles the slurm ``-u`` option in the returned command"""

        app = CrcSqueue()
        slurm_user_argument = f'-u {getpass.getuser()}'

        # The application should default to showing information for the current user
        args, _ = app.parse_known_args([])
        slurm_command = app.build_slurm_command(args)
        self.assertIn(slurm_user_argument, slurm_command, '-u flag is missing from slurm command')

        # Make sure user option is disabled when ``--all`` argument is given
        args, _ = app.parse_known_args(['--all'])
        slurm_command = app.build_slurm_command(args)
        self.assertNotIn(slurm_user_argument, slurm_command, '-u flag was added to slurm command')

    def test_cluster_name(self) -> None:
        """Test the generated slurm command specifies the correct cluster"""

        app = CrcSqueue()

        args, _ = app.parse_known_args([])
        slurm_command = app.build_slurm_command(args)
        self.assertIn('-M all', slurm_command)

        args, _ = app.parse_known_args(['-c', 'smp'])
        slurm_command = app.build_slurm_command(args)
        self.assertIn('-M smp', slurm_command)


class OutputFormat(TestCase):
    """Test the correct output format is specified in the piped slurm command"""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_defaults_to_user_format(self, mock_shell: Mock) -> None:
        """Test the application defaults to using the ``output_format_user`` format"""

        CrcSqueue().execute([])
        executed_command = mock_shell.call_args.args[0]
        self.assertIn(CrcSqueue.output_format_user, executed_command)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_all_flag(self, mock_shell: Mock) -> None:
        """Test the application defaults to using the ``output_format_all`` format"""

        CrcSqueue().execute(['--all'])
        executed_command = mock_shell.call_args.args[0]
        self.assertIn(CrcSqueue.output_format_all, executed_command)


class CommandExecution(TestCase):
    """Test the execution of Slurm commands"""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_slurm_command_executed(self, mock_shell: Mock) -> None:
        """Test the slurm command is executed by the application"""

        # Parse commandline arguments and generate the expected slurm command
        app = CrcSqueue()
        command = app.build_slurm_command(app.parse_args([]))

        # Execute the wrapper and check the slurm command was executed
        app.execute([])
        mock_shell.assert_called_with(command)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('apps.utils.system_info.Shell.run_command')
    def test_slurm_command_printed(self, mock_shell: Mock, mock_stdout: Mock) -> None:
        """Test the slurm command is printed but not executed when ``-z`` is specified"""

        app = CrcSqueue()

        # Parse commandline arguments and generate the expected slurm command
        cli_args = ['-z']
        parsed_args, _ = app.parse_known_args(cli_args)
        command = app.build_slurm_command(parsed_args)

        # Execute the wrapper and check the slurm command was printed but not executed
        app.execute(cli_args)
        self.assertEqual(mock_stdout.getvalue().strip(), command)
        mock_shell.assert_not_called()
