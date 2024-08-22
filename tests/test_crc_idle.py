"""Tests for the `crc-idle` application"""

from argparse import Namespace
from unittest import TestCase
from unittest.mock import call, Mock, patch

from apps.crc_idle import CrcIdle
from apps.utils.system_info import Slurm


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_partition_parsing(self) -> None:
        """Test the application supports parsing multiple cluster partitions"""

        app = CrcIdle()
        args, unknown_args = app.parse_known_args(['-p', 'partition1'])
        self.assertFalse(unknown_args)
        self.assertEqual(['partition1'], args.partition)

        args, unknown_args = app.parse_known_args(['-p', 'partition1', 'partition2'])
        self.assertFalse(unknown_args)
        self.assertEqual(['partition1', 'partition2'], args.partition)

    def test_cluster_parsing(self) -> None:
        """Test argument flags are parsed and stored as cluster names"""

        app = CrcIdle()
        args, unknown_args = app.parse_known_args(['-s', '--mpi'])

        self.assertFalse(unknown_args)
        self.assertTrue(args.smp)
        self.assertTrue(args.mpi)
        self.assertFalse(args.htc)
        self.assertFalse(args.gpu)

    @patch('apps.utils.Slurm.get_cluster_names', new=lambda: tuple(CrcIdle.cluster_types.keys()))
    def test_clusters_default_to_false(self) -> None:
        """Test all cluster flags default to a `False` value"""

        app = CrcIdle()
        args, unknown_args = app.parse_known_args([])

        self.assertFalse(unknown_args)
        for cluster in Slurm.get_cluster_names():
            self.assertFalse(getattr(args, cluster))


class GetClusterList(TestCase):
    """Test the selection of which clusters to print"""

    def test_get_cluster_list_no_arguments(self) -> None:
        """Test returned values when no clusters are specified."""

        app = CrcIdle()
        args = Namespace(smp=False, gpu=False, mpi=False, invest=False, htc=False, partition=None)
        result = app.get_cluster_list(args)

        expected = tuple(app.cluster_types.keys())
        self.assertEqual(expected, result)

    def test_get_cluster_list_with_cluster_arguments(self) -> None:
        """Test returned values when select clusters are specified."""

        app = CrcIdle()
        args = Namespace(smp=True, gpu=False, mpi=True, invest=False, htc=False, partition=None)
        result = app.get_cluster_list(args)

        self.assertEqual(('smp', 'mpi'), result)


class CountIdleResources(TestCase):
    """Test the counting of idle CPU/DPU resources"""

    @patch('apps.utils.Shell.run_command')
    def test_count_idle_cpu_resources(self, mock_run_command: Mock) -> None:
        """Test counting idle CPU resources."""

        cluster = 'smp'
        partition = 'default'
        mock_run_command.return_value = "node1,2/4/0/4,3500\nnode2,3/2/0/3,4000"

        app = CrcIdle()
        result = app.count_idle_resources(cluster, partition)

        expected = {4: {'count': 1, 'min_free_mem': 3500, 'max_free_mem': 3500},
                    2: {'count': 1, 'min_free_mem': 4000, 'max_free_mem': 4000}
                    }
        self.assertEqual(expected, result)

    @patch('apps.utils.Shell.run_command')
    def test_count_idle_gpu_resources(self, mock_run_command: Mock) -> None:
        """Test counting idle GPU resources."""

        cluster = 'gpu'
        partition = 'default'
        mock_run_command.return_value = "node1_4_2_idle_3500\nnode2_4_4_drain_4000"

        app = CrcIdle()
        result = app.count_idle_resources(cluster, partition)
        expected = {2: {'count': 1, 'min_free_mem': 3500, 'max_free_mem': 3500},
                    0: {'count': 1, 'min_free_mem': 4000, 'max_free_mem': 4000}
                    }
        self.assertEqual(expected, result)


class PrintPartitionSummary(TestCase):
    """Test the printing of a partition summary"""

    @patch('builtins.print')
    def test_print_partition_summary_with_idle_resources(self, mock_print: Mock) -> None:
        """Test printing a summary with idle resources."""

        cluster = 'smp'
        partition = 'default'
        idle_resources = {2: {'count': 3, 'min_free_mem': 2500, 'max_free_mem': 3500},
                          4: {'count': 1, 'min_free_mem': 3000, 'max_free_mem': 3000}
                          }  # 3 nodes with 2 idle resources, 1 node with 4 idle resources

        app = CrcIdle()
        app.print_partition_summary(cluster, partition, idle_resources)

        mock_print.assert_has_calls([
            call(f'Cluster: {cluster}, Partition: {partition}'),
            call('=' * 70),
            call('   3 nodes w/   2 idle cores 2.44G - 3.42G min-max free memory'),
            call('   1 nodes w/   4 idle cores 2.93G - 2.93G min-max free memory'),
            call('')
        ], any_order=False)

    @patch('builtins.print')
    def test_print_partition_summary_no_idle_resources(self, mock_print: Mock) -> None:
        """Test printing a summary when no idle resources are available."""

        cluster = 'smp'
        partition = 'default'
        idle_resources = dict()  # No idle resources

        app = CrcIdle()
        app.print_partition_summary(cluster, partition, idle_resources)

        mock_print.assert_any_call(f'Cluster: {cluster}, Partition: {partition}')
        mock_print.assert_any_call('=' * 70)
        mock_print.assert_any_call(' No idle resources')
        mock_print.assert_any_call('')

        mock_print.assert_has_calls([
            call(f'Cluster: {cluster}, Partition: {partition}'),
            call('=====' * 14),
            call(' No idle resources'),
            call('')
        ], any_order=False)
