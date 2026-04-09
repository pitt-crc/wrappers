"""Tests for the ``crc-scancel`` application."""

import getpass
from unittest import TestCase
from unittest.mock import call, patch, Mock

from apps.crc_scancel import CrcScancel
from tests.fixtures import sacct_output


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments."""

    def test_job_id_parsed_as_string(self) -> None:
        """Job ID is stored as a string even though it looks like an integer."""

        args, unknown = CrcScancel().parse_known_args(['1234'])
        self.assertFalse(unknown)
        self.assertEqual('1234', args.job_id)
        self.assertIsInstance(args.job_id, str)

    def test_non_integer_job_id_rejected(self) -> None:
        """Non-integer job IDs raise a SystemExit."""

        with self.assertRaises(SystemExit):
            CrcScancel().parse_args(['not-an-int'])

    def test_float_job_id_truncated_to_int_string(self) -> None:
        """A float string is truncated to its integer part."""

        args, _ = CrcScancel().parse_known_args(['1234'])
        self.assertEqual('1234', args.job_id)


# ---------------------------------------------------------------------------
# get_cluster_for_job_id — command shape and search logic
# ---------------------------------------------------------------------------

class GetClusterForJobId(TestCase):
    """Test that the correct cluster is found for a given job ID."""

    @patch('apps.utils.system_info.Slurm.get_cluster_names')
    @patch('apps.utils.system_info.Shell.run_command')
    def test_returns_cluster_when_job_found(self, mock_run: Mock, mock_clusters: Mock) -> None:
        """Returns the cluster name when the job appears in squeue output."""

        mock_clusters.return_value = {'smp', 'gpu'}
        # squeue returns the job ID only for 'smp'
        def squeue_side_effect(cmd):
            if 'smp' in cmd:
                return '99999 smp my_job R 1:00:00 1 node01'
            return ''

        mock_run.side_effect = squeue_side_effect

        result = CrcScancel().get_cluster_for_job_id('99999')
        self.assertEqual('smp', result)

    @patch('apps.utils.system_info.Slurm.get_cluster_names')
    @patch('apps.utils.system_info.Shell.run_command')
    def test_returns_none_when_job_not_found(self, mock_run: Mock, mock_clusters: Mock) -> None:
        """Returns None when the job ID is not found on any cluster."""

        mock_clusters.return_value = {'smp', 'gpu', 'mpi'}
        mock_run.return_value = ''

        result = CrcScancel().get_cluster_for_job_id('99999')
        self.assertIsNone(result)

    @patch('apps.utils.system_info.Slurm.get_cluster_names')
    @patch('apps.utils.system_info.Shell.run_command')
    def test_searches_all_clusters(self, mock_run: Mock, mock_clusters: Mock) -> None:
        """squeue is called for every cluster returned by get_cluster_names."""

        mock_clusters.return_value = {'smp', 'gpu', 'mpi'}
        mock_run.return_value = ''

        CrcScancel().get_cluster_for_job_id('99999')
        self.assertEqual(3, mock_run.call_count)

    @patch('apps.utils.system_info.Slurm.get_cluster_names')
    @patch('apps.utils.system_info.Shell.run_command')
    def test_squeue_command_includes_user_and_job(self, mock_run: Mock, mock_clusters: Mock) -> None:
        """squeue is called with the current user and the job ID."""

        mock_clusters.return_value = {'smp'}
        mock_run.return_value = ''

        CrcScancel().get_cluster_for_job_id('99999')

        cmd = mock_run.call_args.args[0]
        self.assertIn(getpass.getuser(), cmd)
        self.assertIn('99999', cmd)
        self.assertIn('squeue', cmd)

    @patch('apps.utils.system_info.Slurm.get_cluster_names')
    @patch('apps.utils.system_info.Shell.run_command')
    def test_uses_include_all_clusters(self, mock_run: Mock, mock_clusters: Mock) -> None:
        """get_cluster_names is called with include_all_clusters=True to catch scavenger jobs."""

        mock_clusters.return_value = set()
        mock_run.return_value = ''

        CrcScancel().get_cluster_for_job_id('99999')
        mock_clusters.assert_called_once_with(include_all_clusters=True)


# ---------------------------------------------------------------------------
# cancel_job_on_cluster — command shape
# ---------------------------------------------------------------------------

class CancelJobOnCluster(TestCase):
    """Test the scancel command issued to cancel a job."""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_scancel_command_shape(self, mock_run: Mock) -> None:
        """scancel is called with the correct cluster and job ID."""

        CrcScancel.cancel_job_on_cluster('smp', '99999')

        cmd = mock_run.call_args.args[0]
        self.assertIn('scancel', cmd)
        self.assertIn('-M smp', cmd)
        self.assertIn('99999', cmd)


# ---------------------------------------------------------------------------
# app_logic — confirmation flow
# ---------------------------------------------------------------------------

class AppLogic(TestCase):
    """Test the interactive confirmation and cancellation flow."""

    @patch('apps.utils.system_info.Shell.run_command')
    @patch('apps.utils.system_info.Shell.readchar', return_value='y')
    @patch('apps.utils.system_info.Slurm.get_cluster_names')
    def test_cancels_job_on_confirmation(self, mock_clusters: Mock, mock_readchar: Mock,
                                         mock_run: Mock) -> None:
        """Job is cancelled when the user confirms with 'y'."""

        mock_clusters.return_value = {'smp'}
        mock_run.side_effect = ['99999 smp job R 0:01 1 node01', '']  # squeue, then scancel

        CrcScancel().execute(['99999'])

        # Second call should be scancel
        scancel_cmd = mock_run.call_args_list[1].args[0]
        self.assertIn('scancel', scancel_cmd)

    @patch('apps.utils.system_info.Shell.run_command')
    @patch('apps.utils.system_info.Shell.readchar', return_value='n')
    @patch('apps.utils.system_info.Slurm.get_cluster_names')
    def test_does_not_cancel_on_denial(self, mock_clusters: Mock, mock_readchar: Mock,
                                       mock_run: Mock) -> None:
        """Job is NOT cancelled when the user responds with 'n'."""

        mock_clusters.return_value = {'smp'}
        mock_run.return_value = '99999 smp job R 0:01 1 node01'

        CrcScancel().execute(['99999'])

        # Only one run_command call (the squeue lookup), no scancel
        for c in mock_run.call_args_list:
            self.assertNotIn('scancel', c.args[0])

    @patch('apps.utils.system_info.Slurm.get_cluster_names')
    @patch('apps.utils.system_info.Shell.run_command')
    def test_error_on_missing_job(self, mock_run: Mock, mock_clusters: Mock) -> None:
        """SystemExit is raised when the job is not found on any cluster."""

        mock_clusters.return_value = {'smp', 'gpu'}
        mock_run.return_value = ''

        with self.assertRaises(SystemExit):
            CrcScancel().execute(['99999'])
