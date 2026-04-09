"""Tests for the ``Slurm`` utility class."""

from datetime import date
from unittest import TestCase
from unittest.mock import patch

from apps.utils.system_info import Slurm
from tests.fixtures import sacct_output


# ---------------------------------------------------------------------------
# is_installed
# ---------------------------------------------------------------------------

class IsInstalled(TestCase):
    """Test the ``is_installed()`` method."""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_returns_true_when_sacctmgr_present(self, mock_run) -> None:
        """Returns True when sacctmgr is available and returns a version string."""

        mock_run.return_value = sacct_output.VERSION_STRING
        self.assertTrue(Slurm.is_installed())

    @patch('apps.utils.system_info.Shell.run_command')
    def test_returns_false_when_sacctmgr_missing(self, mock_run) -> None:
        """Returns False when sacctmgr is not on PATH."""

        mock_run.side_effect = FileNotFoundError
        self.assertFalse(Slurm.is_installed())

    @patch('apps.utils.system_info.Shell.run_command')
    def test_calls_sacctmgr(self, mock_run) -> None:
        """is_installed() invokes sacctmgr (not some other binary)."""

        mock_run.return_value = sacct_output.VERSION_STRING
        Slurm.is_installed()
        cmd = mock_run.call_args.args[0]
        self.assertIn('sacctmgr', cmd)


# ---------------------------------------------------------------------------
# get_cluster_names
# ---------------------------------------------------------------------------

class GetClusterNames(TestCase):
    """Test the ``get_cluster_names()`` method."""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_excludes_ignored_clusters_by_default(self, mock_run) -> None:
        """Known ignored clusters (e.g. 'azure') are excluded by default."""

        mock_run.return_value = sacct_output.CLUSTER_NAMES
        clusters = Slurm.get_cluster_names(include_all_clusters=False)
        self.assertNotIn('azure', clusters)
        self.assertIn('smp', clusters)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_includes_ignored_clusters_when_requested(self, mock_run) -> None:
        """All clusters including ignored ones are returned when requested."""

        mock_run.return_value = sacct_output.CLUSTER_NAMES
        clusters = Slurm.get_cluster_names(include_all_clusters=True)
        self.assertIn('azure', clusters)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_empty_output_returns_empty_set(self, mock_run) -> None:
        """Empty sacctmgr output returns an empty collection."""

        mock_run.return_value = sacct_output.CLUSTER_NAMES_EMPTY
        clusters = Slurm.get_cluster_names()
        self.assertEqual(0, len(clusters))


# ---------------------------------------------------------------------------
# get_partition_names
# ---------------------------------------------------------------------------

class GetPartitionNames(TestCase):
    """Test the ``get_partition_names()`` method."""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_excludes_ignored_partitions_by_default(self, mock_run) -> None:
        """Personal/ignored partitions are excluded by default."""

        mock_run.return_value = sacct_output.PARTITION_NAMES
        partitions = Slurm.get_partition_names('smp', include_all_partitions=False)
        self.assertNotIn('pliu', partitions)
        self.assertIn('smp', partitions)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_includes_ignored_partitions_when_requested(self, mock_run) -> None:
        """All partitions including ignored ones are returned when requested."""

        mock_run.return_value = sacct_output.PARTITION_NAMES
        partitions = Slurm.get_partition_names('smp', include_all_partitions=True)
        self.assertIn('pliu', partitions)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_command_targets_correct_cluster(self, mock_run) -> None:
        """get_partition_names() passes the cluster name to the underlying command."""

        mock_run.return_value = sacct_output.PARTITION_NAMES_SINGLE
        Slurm.get_partition_names('mpi')
        cmd = mock_run.call_args.args[0]
        self.assertIn('mpi', cmd)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_empty_output_returns_empty_set(self, mock_run) -> None:
        """Empty output returns an empty collection."""

        mock_run.return_value = sacct_output.PARTITION_NAMES_EMPTY
        partitions = Slurm.get_partition_names('smp')
        self.assertEqual(0, len(partitions))


# ---------------------------------------------------------------------------
# check_slurm_account_exists
# ---------------------------------------------------------------------------

class CheckSlurmAccountExists(TestCase):
    """Test the ``check_slurm_account_exists()`` method."""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_no_error_when_account_exists(self, mock_run) -> None:
        """No exception is raised when the account is found."""

        mock_run.return_value = sacct_output.ACCOUNT_EXISTS
        Slurm.check_slurm_account_exists('mygroup')  # must not raise

    @patch('apps.utils.system_info.Shell.run_command')
    def test_raises_runtime_error_when_account_missing(self, mock_run) -> None:
        """RuntimeError is raised when sacctmgr returns no output for the account."""

        mock_run.return_value = sacct_output.ACCOUNT_NOT_FOUND
        with self.assertRaises(RuntimeError):
            Slurm.check_slurm_account_exists('nonexistent')

    @patch('apps.utils.system_info.Shell.run_command')
    def test_command_includes_account_name(self, mock_run) -> None:
        """The account name is passed to the underlying sacctmgr query."""

        mock_run.return_value = sacct_output.ACCOUNT_EXISTS
        Slurm.check_slurm_account_exists('mygroup')
        cmd = mock_run.call_args.args[0]
        self.assertIn('mygroup', cmd)


# ---------------------------------------------------------------------------
# get_cluster_usage_by_user
# ---------------------------------------------------------------------------

class GetClusterUsageByUser(TestCase):
    """Test the ``get_cluster_usage_by_user()`` method."""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_parses_multi_user_output(self, mock_run) -> None:
        """Multiple user rows and a group total are parsed correctly."""

        mock_run.return_value = sacct_output.USAGE_MULTI_USER
        usage = Slurm.get_cluster_usage_by_user('account1', date(2023, 1, 1), 'smp')

        self.assertEqual({'user1': 100, 'user2': 200, 'total': '300'}, usage)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_parses_single_user_output(self, mock_run) -> None:
        """A single-user output is parsed correctly."""

        mock_run.return_value = sacct_output.USAGE_SINGLE_USER
        usage = Slurm.get_cluster_usage_by_user('account1', date(2023, 1, 1), 'smp')

        self.assertIn('user1', usage)
        self.assertIn('total', usage)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_returns_none_for_empty_output(self, mock_run) -> None:
        """None is returned when sacct produces no output."""

        mock_run.return_value = sacct_output.USAGE_EMPTY
        usage = Slurm.get_cluster_usage_by_user('account1', date(2023, 1, 1), 'smp')
        self.assertIsNone(usage)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_returns_none_on_value_error(self, mock_run) -> None:
        """None is returned (not raised) when parsing fails."""

        mock_run.side_effect = ValueError
        usage = Slurm.get_cluster_usage_by_user('account1', date(2023, 1, 1), 'smp')
        self.assertIsNone(usage)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_command_includes_cluster_and_account(self, mock_run) -> None:
        """The sacct command targets the correct cluster and account."""

        mock_run.return_value = sacct_output.USAGE_MULTI_USER
        Slurm.get_cluster_usage_by_user('myaccount', date(2023, 1, 1), 'gpu')

        cmd = mock_run.call_args.args[0]
        self.assertIn('gpu', cmd)
        self.assertIn('myaccount', cmd)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_command_includes_start_date(self, mock_run) -> None:
        """The sacct command includes the start date for the query window."""

        mock_run.return_value = sacct_output.USAGE_MULTI_USER
        start = date(2023, 6, 15)
        Slurm.get_cluster_usage_by_user('myaccount', start, 'smp')

        cmd = mock_run.call_args.args[0]
        self.assertIn('2023', cmd)
