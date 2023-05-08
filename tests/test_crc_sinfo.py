"""Tests for the ``CrcSinfo`` class."""

from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch

from apps.crc_sinfo import CrcSinfo


class CommandExecution(TestCase):
    """Test the execution/printing of Slurm commands"""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_all_clusters(self, mock_shell: Mock) -> None:
        """Test all clusters are included in the slurm command by default"""

        CrcSinfo().execute()
        mock_shell.assert_called_with('sinfo -M all')

    @patch('apps.utils.system_info.Shell.run_command')
    def test_custom_cluster(self, mock_shell: Mock) -> None:
        """Test the ``--cluster`` argument is passed to Slurm"""

        CrcSinfo().execute(['-c', 'mpi'])
        mock_shell.assert_called_with('sinfo -M mpi')

        CrcSinfo().execute(['--cluster', 'mpi'])
        mock_shell.assert_called_with('sinfo -M mpi')

    @patch('sys.stdout', new_callable=StringIO)
    @patch('apps.utils.system_info.Shell.run_command')
    def test_command_is_printed(self, mock_shell: Mock, mock_stdout: Mock) -> None:
        """Test the ``slurm`` command is printed but not executed when ``-z`` is specified"""

        CrcSinfo().execute(['-z'])
        self.assertEqual('sinfo -M all', mock_stdout.getvalue().strip())
        mock_shell.assert_not_called()

        # Clear the mock STDIN object
        mock_stdout.seek(0)
        mock_stdout.truncate(0)

        CrcSinfo().execute(['--print-command'])
        self.assertEqual('sinfo -M all', mock_stdout.getvalue().strip())
        mock_shell.assert_not_called()
