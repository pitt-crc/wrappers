"""Tests for the ``crc-sinfo`` application."""

from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch

from apps.crc_sinfo import CrcSinfo


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments."""

    def test_cluster_defaults_to_all(self) -> None:
        """Cluster defaults to 'all' when not specified."""

        args, _ = CrcSinfo().parse_known_args([])
        self.assertEqual('all', args.cluster)

    def test_custom_cluster_short_flag(self) -> None:
        args, _ = CrcSinfo().parse_known_args(['-c', 'mpi'])
        self.assertEqual('mpi', args.cluster)

    def test_custom_cluster_long_flag(self) -> None:
        args, _ = CrcSinfo().parse_known_args(['--cluster', 'mpi'])
        self.assertEqual('mpi', args.cluster)

    def test_print_command_defaults_to_false(self) -> None:
        args, _ = CrcSinfo().parse_known_args([])
        self.assertFalse(args.print_command)

    def test_print_command_short_flag(self) -> None:
        args, _ = CrcSinfo().parse_known_args(['-z'])
        self.assertTrue(args.print_command)

    def test_print_command_long_flag(self) -> None:
        args, _ = CrcSinfo().parse_known_args(['--print-command'])
        self.assertTrue(args.print_command)


# ---------------------------------------------------------------------------
# Command shape and execution
# ---------------------------------------------------------------------------

class CommandExecution(TestCase):
    """Test the sinfo command issued and whether it is printed or executed."""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_default_targets_all_clusters(self, mock_run: Mock) -> None:
        """Default invocation calls sinfo -M all."""

        mock_run.return_value = ''
        CrcSinfo().execute([])
        mock_run.assert_called_with('sinfo -M all')

    @patch('apps.utils.system_info.Shell.run_command')
    def test_custom_cluster_in_command(self, mock_run: Mock) -> None:
        """The specified cluster name is passed to sinfo via -M."""

        mock_run.return_value = ''
        CrcSinfo().execute(['-c', 'mpi'])
        mock_run.assert_called_with('sinfo -M mpi')

    @patch('apps.utils.system_info.Shell.run_command')
    def test_long_cluster_flag(self, mock_run: Mock) -> None:
        mock_run.return_value = ''
        CrcSinfo().execute(['--cluster', 'gpu'])
        mock_run.assert_called_with('sinfo -M gpu')

    @patch('sys.stdout', new_callable=StringIO)
    @patch('apps.utils.system_info.Shell.run_command')
    def test_print_command_short_flag_prints_and_skips_execution(
        self, mock_run: Mock, mock_stdout: Mock
    ) -> None:
        """-z prints the command to stdout without executing it."""

        CrcSinfo().execute(['-z'])
        self.assertEqual('sinfo -M all', mock_stdout.getvalue().strip())
        mock_run.assert_not_called()

    @patch('sys.stdout', new_callable=StringIO)
    @patch('apps.utils.system_info.Shell.run_command')
    def test_print_command_long_flag_prints_and_skips_execution(
        self, mock_run: Mock, mock_stdout: Mock
    ) -> None:
        """--print-command prints the command to stdout without executing it."""

        CrcSinfo().execute(['--print-command'])
        self.assertEqual('sinfo -M all', mock_stdout.getvalue().strip())
        mock_run.assert_not_called()

    @patch('sys.stdout', new_callable=StringIO)
    @patch('apps.utils.system_info.Shell.run_command')
    def test_print_command_with_custom_cluster(
        self, mock_run: Mock, mock_stdout: Mock
    ) -> None:
        """Printed command reflects the specified cluster."""

        CrcSinfo().execute(['-z', '-c', 'smp'])
        self.assertEqual('sinfo -M smp', mock_stdout.getvalue().strip())
        mock_run.assert_not_called()
