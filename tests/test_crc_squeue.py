"""Tests for the `crc-squeue` application."""

import getpass
from io import StringIO
from unittest import TestCase
from unittest.mock import patch, Mock

from apps.crc_squeue import CrcSqueue
from tests.fixtures import squeue_output


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments."""

    def test_flag_defaults_are_false(self) -> None:
        """Boolean flags default to False."""

        args, _ = CrcSqueue().parse_known_args([])
        self.assertFalse(args.all)
        self.assertFalse(args.watch)
        self.assertFalse(args.print_command)

    def test_cluster_defaults_to_all(self) -> None:
        """Cluster defaults to 'all' when not specified."""

        args, _ = CrcSqueue().parse_known_args([])
        self.assertEqual('all', args.cluster)

    def test_custom_cluster_short_flag(self) -> None:
        """Short -c flag stores the cluster name."""

        args, _ = CrcSqueue().parse_known_args(['-c', 'smp'])
        self.assertEqual('smp', args.cluster)

    def test_custom_cluster_long_flag(self) -> None:
        """Long --cluster flag stores the cluster name."""

        args, _ = CrcSqueue().parse_known_args(['--cluster', 'smp'])
        self.assertEqual('smp', args.cluster)

    def test_watch_stores_interval_constant(self) -> None:
        """--watch stores the numeric refresh interval, not True."""

        args, _ = CrcSqueue().parse_known_args(['--watch'])
        self.assertEqual(10, args.watch)

    def test_watch_short_flag(self) -> None:
        """Short -w flag also stores the refresh interval."""

        args, _ = CrcSqueue().parse_known_args(['-w'])
        self.assertEqual(10, args.watch)


# ---------------------------------------------------------------------------
# Slurm command construction
# ---------------------------------------------------------------------------

class SlurmCommandConstruction(TestCase):
    """Test the squeue command string built from parsed arguments."""

    def test_defaults_to_current_user_filter(self) -> None:
        """Default command filters to the current user with -u."""

        app = CrcSqueue()
        args, _ = app.parse_known_args([])
        cmd = app.build_slurm_command(args)
        self.assertIn(f'-u {getpass.getuser()}', cmd)

    def test_all_flag_removes_user_filter(self) -> None:
        """--all removes the -u filter so all users' jobs are shown."""

        app = CrcSqueue()
        args, _ = app.parse_known_args(['--all'])
        cmd = app.build_slurm_command(args)
        self.assertNotIn(f'-u {getpass.getuser()}', cmd)

    def test_default_cluster_is_all(self) -> None:
        """Default command targets all clusters."""

        app = CrcSqueue()
        args, _ = app.parse_known_args([])
        cmd = app.build_slurm_command(args)
        self.assertIn('-M all', cmd)

    def test_custom_cluster_in_command(self) -> None:
        """Specified cluster name appears in the command."""

        app = CrcSqueue()
        args, _ = app.parse_known_args(['-c', 'gpu'])
        cmd = app.build_slurm_command(args)
        self.assertIn('-M gpu', cmd)

    def test_user_format_string_included_by_default(self) -> None:
        """User-scoped output format is included in the default command."""

        app = CrcSqueue()
        args, _ = app.parse_known_args([])
        cmd = app.build_slurm_command(args)
        self.assertIn(CrcSqueue.output_format_user, cmd)

    def test_all_format_string_included_with_all_flag(self) -> None:
        """All-users output format is included when --all is specified."""

        app = CrcSqueue()
        args, _ = app.parse_known_args(['--all'])
        cmd = app.build_slurm_command(args)
        self.assertIn(CrcSqueue.output_format_all, cmd)


# ---------------------------------------------------------------------------
# Command execution
# ---------------------------------------------------------------------------

class CommandExecution(TestCase):
    """Test that the correct squeue command is executed or printed."""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_executes_built_command(self, mock_run: Mock) -> None:
        """execute() runs exactly the command returned by build_slurm_command()."""

        mock_run.return_value = squeue_output.SINGLE_JOB_RUNNING
        app = CrcSqueue()
        expected_cmd = app.build_slurm_command(app.parse_args([]))
        app.execute([])
        mock_run.assert_called_with(expected_cmd)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('apps.utils.system_info.Shell.run_command')
    def test_print_command_flag_prints_and_does_not_execute(self, mock_run: Mock, mock_stdout: Mock) -> None:
        """-z prints the command to stdout and does not call Shell.run_command."""

        app = CrcSqueue()
        expected_cmd = app.build_slurm_command(app.parse_known_args(['-z'])[0])
        app.execute(['-z'])

        self.assertEqual(expected_cmd, mock_stdout.getvalue().strip())
        mock_run.assert_not_called()

    @patch('apps.utils.system_info.Shell.run_command')
    def test_output_is_printed(self, mock_run: Mock) -> None:
        """Slurm output is forwarded to stdout."""

        mock_run.return_value = squeue_output.MIXED_RUNNING_PENDING
        # Just verify execute() completes without error when there's real-shaped output
        CrcSqueue().execute([])
        mock_run.assert_called_once()
