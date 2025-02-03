"""Tests for the ``Slurm`` class"""

from unittest import TestCase
from unittest.mock import patch, MagicMock
from datetime import date
from apps.utils.system_info import Slurm, Shell

class TestSlurm(TestCase):

    @patch('apps.utils.system_info.Shell.run_command')
    def test_is_installed(self, mock_run_command):
        # sacctmgr is installed
        mock_run_command.return_value = "slurm 22.05.11"
        self.assertTrue(Slurm.is_installed())

        # sacctmgr is not installed
        mock_run_command.side_effect = FileNotFoundError
        self.assertFalse(Slurm.is_installed())

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_cluster_names(self, mock_run_command):
        # Mock the output of squeue command
        mock_run_command.return_value = "CLUSTER: cluster1\nCLUSTER: cluster2\nCLUSTER: azure\n"

        # Test without including ignored clusters
        clusters = Slurm.get_cluster_names(include_all_clusters=False)
        self.assertEqual(clusters, {'cluster1', 'cluster2'})

        # Test including ignored clusters
        clusters = Slurm.get_cluster_names(include_all_clusters=True)
        self.assertEqual(clusters, {'cluster1', 'cluster2', 'azure'})

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_partition_names(self, mock_run_command):
        # Mock the output of scontrol command
        mock_run_command.return_value = "PartitionName=partition1\nPartitionName=partition2\nPartitionName=pliu\n"

        # Test without including ignored partitions
        partitions = Slurm.get_partition_names('cluster1', include_all_partitions=False)
        self.assertEqual(partitions, {'partition1', 'partition2'})

        # Test including ignored partitions
        partitions = Slurm.get_partition_names('cluster1', include_all_partitions=True)
        self.assertEqual(partitions, {'partition1', 'partition2', 'pliu'})

    @patch('apps.utils.system_info.Shell.run_command')
    def test_check_slurm_account_exists(self, mock_run_command):
        # Test when account exists
        mock_run_command.return_value = "account1"
        Slurm.check_slurm_account_exists('account1')  # Should not raise an exception

        # Test when account does not exist
        mock_run_command.return_value = ""
        with self.assertRaises(RuntimeError):
            Slurm.check_slurm_account_exists('nonexistent_account')

    @patch('apps.utils.system_info.Shell.run_command')
    def test_get_cluster_usage_by_user(self, mock_run_command):
        # Mock the output of sreport command
        mock_run_command.return_value = "user1|100\nuser2|200\n|300"

        # Test with valid data
        start_date = date(2023, 1, 1)
        usage = Slurm.get_cluster_usage_by_user('account1', start_date, 'cluster1')
        expected_usage = {
            'user1': 100,
            'user2': 200,
            'total': '300'
        }
        self.assertEqual(usage, expected_usage)

        # Test with no data
        mock_run_command.return_value = ""
        usage = Slurm.get_cluster_usage_by_user('account1', start_date, 'cluster1')
        self.assertIsNone(usage)

        # Test with ValueError
        mock_run_command.side_effect = ValueError
        usage = Slurm.get_cluster_usage_by_user('account1', start_date, 'cluster1')
        self.assertIsNone(usage)

if __name__ == '__main__':
    unittest.main()

