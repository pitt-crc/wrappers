""" Tests for the `Slurm` class """
from datetime import date
from unittest import TestCase
from unittest.mock import patch

from apps.utils.system_info import Slurm


class IsInstalled(TestCase):
    """ Tests for the `is_installed()` function of the `Slurm` class """

    @patch('apps.utils.system_info.Shell.run_command')
    def test_slurm_installed(self, mock_run_command) -> None:
        """ Test that `is_installed()` returns `True` when `sacctmgr` is installed """

        mock_run_command.return_value = "slurm 22.05.11"
        self.assertTrue(Slurm.is_installed())

    @patch('apps.utils.system_info.Shell.run_command')
    def test_slurm_not_installed(self, mock_run_command) -> None:
        """ Test that `is_installed()` returns `False` when `sacctmgr` is not installed """

        mock_run_command.side_effect = FileNotFoundError
        self.assertFalse(Slurm.is_installed())


class GetClusterNames(TestCase):
    """ Tests for the `get_cluster_names()` method of the `Slurm` class """

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_cluster_names_without_ignored(self, mock_run_command) -> None:
        """ Test that `get_cluster_names()` excludes ignored clusters when `include_all_clusters=False` """

        mock_run_command.return_value = "CLUSTER: cluster1\nCLUSTER: cluster2\nCLUSTER: azure\n"

        clusters = Slurm.get_cluster_names(include_all_clusters=False)
        self.assertEqual(clusters, {'cluster1', 'cluster2'})

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_cluster_names_with_ignored(self, mock_run_command) -> None:
        """ Test that `get_cluster_names()` includes ignored clusters when `include_all_clusters=True` """

        mock_run_command.return_value = "CLUSTER: cluster1\nCLUSTER: cluster2\nCLUSTER: azure\n"

        clusters = Slurm.get_cluster_names(include_all_clusters=True)
        self.assertEqual(clusters, {'cluster1', 'cluster2', 'azure'})


class GetPartitionNames(TestCase):
    """ Test cases for the `get_partition_names()` method of the `Slurm` class """

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_partition_names_without_ignored(self, mock_run_command) -> None:
        """ Test that `get_partition_names()` excludes ignored partitions when `include_all_partitions=False` """

        mock_run_command.return_value = "PartitionName=partition1\nPartitionName=partition2\nPartitionName=pliu\n"

        partitions = Slurm.get_partition_names('cluster1', include_all_partitions=False)
        self.assertEqual(partitions, {'partition1', 'partition2'})

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_partition_names_with_ignored(self, mock_run_command) -> None:
        """ Test that `get_partition_names()` includes ignored partitions when `include_all_partitions=True` """

        mock_run_command.return_value = "PartitionName=partition1\nPartitionName=partition2\nPartitionName=pliu\n"

        partitions = Slurm.get_partition_names('cluster1', include_all_partitions=True)
        self.assertEqual(partitions, {'partition1', 'partition2', 'pliu'})


class CheckSlurmAccountExists(TestCase):
    """ Test cases for the `check_slurm_account_exists()` method of the `Slurm` class """

    @patch('apps.utils.system_info.Shell.run_command')
    def test_account_exists(self, mock_run_command) -> None:
        """ Test that `check_slurm_account_exists()` does not raise an error when the account exists """
        mock_run_command.return_value = "account1"
        Slurm.check_slurm_account_exists('account1')  # Should not raise an exception

    @patch('apps.utils.system_info.Shell.run_command')
    def test_account_does_not_exist(self, mock_run_command) -> None:
        """ Test that `check_slurm_account_exists()` raises a `RuntimeError` when the account does not exist """
        mock_run_command.return_value = ""
        with self.assertRaises(RuntimeError):
            Slurm.check_slurm_account_exists('nonexistent_account')


class GetClusterUsageByUser(TestCase):
    """ Test cases for the `get_cluster_usage_by_user()` method of the `Slurm` class """

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_cluster_usage_with_valid_data(self, mock_run_command) -> None:
        """ Test that `get_cluster_usage_by_user()` returns the correct usage data when valid data is provided """

        mock_run_command.return_value = "user1|100\nuser2|200\n|300"
        start_date = date(2023, 1, 1)

        usage = Slurm.get_cluster_usage_by_user('account1', start_date, 'cluster1')
        expected_usage = {
            'user1': 100,
            'user2': 200,
            'total': '300'
        }
        self.assertEqual(usage, expected_usage)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_cluster_usage_with_no_data(self, mock_run_command) -> None:
        """ Test that `get_cluster_usage_by_user()` returns `None` when no data is available """

        mock_run_command.return_value = ""
        start_date = date(2023, 1, 1)

        usage = Slurm.get_cluster_usage_by_user('account1', start_date, 'cluster1')
        self.assertIsNone(usage)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_cluster_usage_with_value_error(self, mock_run_command) -> None:
        """ Test that `get_cluster_usage_by_user()` returns `None` when a `ValueError` occurs """

        mock_run_command.side_effect = ValueError
        start_date = date(2023, 1, 1)

        usage = Slurm.get_cluster_usage_by_user('account1', start_date, 'cluster1')
        self.assertIsNone(usage)
