"""Tests for the `crc-idle` application."""

from argparse import Namespace
from unittest import TestCase
from unittest.mock import call, Mock, patch

from apps.crc_idle import CrcIdle
from apps.utils.system_info import Slurm
from tests.fixtures import sinfo_cpu_nodes, sinfo_gpu_nodes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_idle_app() -> CrcIdle:
    return CrcIdle()


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments."""

    def test_partition_parsing(self) -> None:
        """Test the application supports parsing multiple cluster partitions."""

        app = _make_idle_app()
        args, unknown = app.parse_known_args(['-p', 'partition1'])
        self.assertFalse(unknown)
        self.assertEqual(['partition1'], args.partition)

        args, unknown = app.parse_known_args(['-p', 'partition1', 'partition2'])
        self.assertFalse(unknown)
        self.assertEqual(['partition1', 'partition2'], args.partition)

    def test_cluster_flag_parsing(self) -> None:
        """Test short and long cluster flags are stored under the correct attribute names."""

        app = _make_idle_app()
        args, unknown = app.parse_known_args(['-s', '--mpi'])

        self.assertFalse(unknown)
        self.assertTrue(args.smp)
        self.assertTrue(args.mpi)
        self.assertFalse(args.htc)
        self.assertFalse(args.gpu)
        self.assertFalse(args.teach)

    @patch('apps.utils.Slurm.get_cluster_names', new=lambda: tuple(CrcIdle.cluster_types.keys()))
    def test_cluster_flags_default_to_false(self) -> None:
        """Test all cluster flags default to False when no arguments are given."""

        app = _make_idle_app()
        args, unknown = app.parse_known_args([])

        self.assertFalse(unknown)
        for cluster in Slurm.get_cluster_names():
            self.assertFalse(getattr(args, cluster))

    def test_partition_defaults_to_none(self) -> None:
        """Test the partition argument defaults to None."""

        args, _ = _make_idle_app().parse_known_args([])
        self.assertIsNone(args.partition)


# ---------------------------------------------------------------------------
# Cluster selection logic
# ---------------------------------------------------------------------------

class GetClusterList(TestCase):
    """Test which clusters are selected for reporting."""

    def test_defaults_to_all_known_clusters(self) -> None:
        """All known clusters are returned when none are explicitly requested."""

        app = _make_idle_app()
        args = Namespace(smp=False, gpu=False, mpi=False, htc=False, teach=False, partition=None)
        self.assertEqual(tuple(app.cluster_types.keys()), app.get_cluster_list(args))

    def test_returns_only_specified_clusters(self) -> None:
        """Only the requested clusters are returned."""

        app = _make_idle_app()
        args = Namespace(smp=True, gpu=False, mpi=True, htc=False, teach=False, partition=None)
        self.assertEqual(('smp', 'mpi'), app.get_cluster_list(args))


# ---------------------------------------------------------------------------
# Slurm command shape
# ---------------------------------------------------------------------------

class SlurmCommandShape(TestCase):
    """Test that the correct sinfo commands are issued for each cluster/partition."""

    @patch('apps.utils.Shell.run_command')
    def test_cpu_cluster_command_format(self, mock_run: Mock) -> None:
        """CPU sinfo call uses %N,%C,%e,%t format fields."""

        mock_run.return_value = sinfo_cpu_nodes.EMPTY
        CrcIdle()._count_idle_cpu_resources('smp', 'smp')

        cmd = mock_run.call_args.args[0]
        self.assertIn('-M smp', cmd)
        self.assertIn('-p smp', cmd)
        self.assertIn('%N,%C,%e,%t', cmd)
        self.assertIn('-N', cmd)

    @patch('apps.utils.Shell.run_command')
    def test_gpu_cluster_command_format(self, mock_run: Mock) -> None:
        """GPU sinfo call uses the NodeList/gres/gresUsed/StateCompact/FreeMem format."""

        mock_run.return_value = sinfo_gpu_nodes.EMPTY
        CrcIdle()._count_idle_gpu_resources('gpu', 'default')

        cmd = mock_run.call_args.args[0]
        self.assertIn('-M gpu', cmd)
        self.assertIn('-p default', cmd)
        self.assertIn('NodeList', cmd)
        self.assertIn('gres', cmd)
        self.assertIn('FreeMem', cmd)


# ---------------------------------------------------------------------------
# CPU resource counting — output parsing
# ---------------------------------------------------------------------------

class CountIdleCpuResources(TestCase):
    """Test parsing of sinfo CPU-node output into idle-resource counts."""

    @patch('apps.utils.Shell.run_command')
    def test_mixed_healthy_nodes(self, mock_run: Mock) -> None:
        """Two healthy nodes with different idle counts are counted separately."""

        mock_run.return_value = sinfo_cpu_nodes.MIXED_HEALTHY
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        # MIXED_HEALTHY: node1 has 4 idle @ 3500 MB, node2 has 2 idle @ 4000 MB
        self.assertIn(4, result)
        self.assertIn(2, result)
        self.assertEqual(1, result[4]['count'])
        self.assertEqual(1, result[2]['count'])

    @patch('apps.utils.Shell.run_command')
    def test_fully_idle_node(self, mock_run: Mock) -> None:
        """A completely idle node reports all cores as available."""

        mock_run.return_value = sinfo_cpu_nodes.FULLY_IDLE
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertIn(8, result)
        self.assertEqual(1, result[8]['count'])

    @patch('apps.utils.Shell.run_command')
    def test_fully_allocated_node(self, mock_run: Mock) -> None:
        """A fully allocated node reports zero idle cores."""

        mock_run.return_value = sinfo_cpu_nodes.FULLY_ALLOCATED
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertIn(0, result)

    @patch('apps.utils.Shell.run_command')
    def test_multiple_nodes_same_idle_count_are_aggregated(self, mock_run: Mock) -> None:
        """Nodes sharing the same idle count are summed into one entry."""

        mock_run.return_value = sinfo_cpu_nodes.MULTIPLE_NODES_SAME_IDLE
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertEqual(3, result[4]['count'])

    @patch('apps.utils.Shell.run_command')
    def test_multiple_nodes_memory_min_max_tracked(self, mock_run: Mock) -> None:
        """Min and max free memory are tracked correctly across aggregated nodes."""

        mock_run.return_value = sinfo_cpu_nodes.MULTIPLE_NODES_SAME_IDLE
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertEqual(3000, result[4]['min_free_mem'])
        self.assertEqual(4000, result[4]['max_free_mem'])

    @patch('apps.utils.Shell.run_command')
    def test_down_node_reports_zero(self, mock_run: Mock) -> None:
        """A downed node is reported as having zero idle resources."""

        mock_run.return_value = sinfo_cpu_nodes.SINGLE_DOWN
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertIn(0, result)
        self.assertEqual(0, result[0]['min_free_mem'])
        self.assertEqual(0, result[0]['max_free_mem'])

    @patch('apps.utils.Shell.run_command')
    def test_drained_node_reports_zero(self, mock_run: Mock) -> None:
        """A drained node is reported as having zero idle resources."""

        mock_run.return_value = sinfo_cpu_nodes.SINGLE_DRAIN
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertIn(0, result)

    @patch('apps.utils.Shell.run_command')
    def test_all_down_nodes_merged(self, mock_run: Mock) -> None:
        """Multiple downed nodes are all counted under zero idle resources."""

        mock_run.return_value = sinfo_cpu_nodes.ALL_DOWN
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertEqual(1, len(result))
        self.assertEqual(2, result[0]['count'])

    @patch('apps.utils.Shell.run_command')
    def test_mixed_healthy_and_down(self, mock_run: Mock) -> None:
        """Healthy and downed nodes in the same partition are counted separately."""

        mock_run.return_value = sinfo_cpu_nodes.MIXED_DOWN_AND_DRAIN
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertIn(4, result)   # healthy node
        self.assertIn(0, result)   # down + drain nodes

    @patch('apps.utils.Shell.run_command')
    def test_free_mem_not_available_treated_as_zero(self, mock_run: Mock) -> None:
        """'N/A' free memory is treated as 0 rather than raising an error."""

        mock_run.return_value = sinfo_cpu_nodes.FREE_MEM_NOT_AVAILABLE
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertEqual(0, result[8]['min_free_mem'])
        self.assertEqual(0, result[8]['max_free_mem'])

    @patch('apps.utils.Shell.run_command')
    def test_empty_output_returns_empty_dict(self, mock_run: Mock) -> None:
        """Empty sinfo output returns an empty dictionary without raising."""

        mock_run.return_value = sinfo_cpu_nodes.EMPTY
        result = _make_idle_app().count_idle_resources('smp', 'smp')

        self.assertEqual({}, result)


# ---------------------------------------------------------------------------
# GPU resource counting — output parsing
# ---------------------------------------------------------------------------

class CountIdleGpuResources(TestCase):
    """Test parsing of sinfo GPU-node output into idle-resource counts."""

    @patch('apps.utils.Shell.run_command')
    def test_mixed_healthy_nodes(self, mock_run: Mock) -> None:
        """Two nodes: one with 2 idle GPUs, one fully allocated."""

        mock_run.return_value = sinfo_gpu_nodes.MIXED_HEALTHY
        result = _make_idle_app().count_idle_resources('gpu', 'default')

        self.assertIn(2, result)
        self.assertIn(0, result)

    @patch('apps.utils.Shell.run_command')
    def test_fully_idle_node(self, mock_run: Mock) -> None:
        """All GPUs are idle."""

        mock_run.return_value = sinfo_gpu_nodes.FULLY_IDLE
        result = _make_idle_app().count_idle_resources('gpu', 'default')

        self.assertIn(4, result)

    @patch('apps.utils.Shell.run_command')
    def test_multiple_nodes_same_idle_count_are_aggregated(self, mock_run: Mock) -> None:
        """Nodes with the same idle GPU count are aggregated."""

        mock_run.return_value = sinfo_gpu_nodes.MULTIPLE_NODES_SAME_IDLE
        result = _make_idle_app().count_idle_resources('gpu', 'default')

        self.assertEqual(3, result[2]['count'])
        self.assertEqual(3000, result[2]['min_free_mem'])
        self.assertEqual(4000, result[2]['max_free_mem'])

    @patch('apps.utils.Shell.run_command')
    def test_drained_node_reports_zero(self, mock_run: Mock) -> None:
        """A drained GPU node is reported as having zero idle GPUs."""

        mock_run.return_value = sinfo_gpu_nodes.SINGLE_DRAIN
        result = _make_idle_app().count_idle_resources('gpu', 'default')

        self.assertIn(0, result)
        self.assertEqual(0, result[0]['min_free_mem'])

    @patch('apps.utils.Shell.run_command')
    def test_both_drain_state_variants_handled(self, mock_run: Mock) -> None:
        """Both 'drain' and 'drain*' state strings are treated as drained."""

        mock_run.return_value = sinfo_gpu_nodes.MIXED_DRAIN_VARIANTS
        result = _make_idle_app().count_idle_resources('gpu', 'default')

        self.assertEqual(1, len(result))
        self.assertEqual(2, result[0]['count'])

    @patch('apps.utils.Shell.run_command')
    def test_free_mem_not_available_treated_as_zero(self, mock_run: Mock) -> None:
        """'N/A' free memory is treated as 0."""

        mock_run.return_value = sinfo_gpu_nodes.FREE_MEM_NOT_AVAILABLE
        result = _make_idle_app().count_idle_resources('gpu', 'default')

        self.assertEqual(0, result[4]['min_free_mem'])

    @patch('apps.utils.Shell.run_command')
    def test_empty_output_returns_empty_dict(self, mock_run: Mock) -> None:
        """Empty sinfo output returns an empty dictionary without raising."""

        mock_run.return_value = sinfo_gpu_nodes.EMPTY
        result = _make_idle_app().count_idle_resources('gpu', 'default')

        self.assertEqual({}, result)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

class PrintPartitionSummary(TestCase):
    """Test the human-readable summary printed for each partition."""

    @patch('builtins.print')
    def test_header_always_printed(self, mock_print: Mock) -> None:
        """Cluster and partition header is printed regardless of resource count."""

        app = _make_idle_app()
        app.print_partition_summary('smp', 'default', {})
        mock_print.assert_any_call('Cluster: smp, Partition: default')

    @patch('builtins.print')
    def test_separator_line_is_70_chars(self, mock_print: Mock) -> None:
        """Separator line is exactly 70 '=' characters."""

        _make_idle_app().print_partition_summary('smp', 'default', {})
        mock_print.assert_any_call('=' * 70)

    @patch('builtins.print')
    def test_no_resources_message(self, mock_print: Mock) -> None:
        """'No idle resources' message is printed when the dict is empty."""

        _make_idle_app().print_partition_summary('smp', 'default', {})
        mock_print.assert_any_call(' No idle resources')

    @patch('builtins.print')
    def test_cpu_resources_full_output_order(self, mock_print: Mock) -> None:
        """CPU resource rows are printed in ascending idle-count order with correct values."""

        idle_resources = {
            2: {'count': 3, 'min_free_mem': 2500, 'max_free_mem': 3500},
            4: {'count': 1, 'min_free_mem': 3000, 'max_free_mem': 3000},
        }
        _make_idle_app().print_partition_summary('smp', 'default', idle_resources)

        mock_print.assert_has_calls([
            call('Cluster: smp, Partition: default'),
            call('=' * 70),
            call('   3 nodes w/   2 idle cores 2.44G - 3.42G min-max free memory'),
            call('   1 nodes w/   4 idle cores 2.93G - 2.93G min-max free memory'),
            call(''),
        ], any_order=False)

    @patch('builtins.print')
    def test_gpu_resources_label(self, mock_print: Mock) -> None:
        """GPU clusters use 'GPUs' as the resource label instead of 'cores'."""

        idle_resources = {2: {'count': 1, 'min_free_mem': 4096, 'max_free_mem': 4096}}
        _make_idle_app().print_partition_summary('gpu', 'default', idle_resources)

        printed = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('GPUs', printed)
        self.assertNotIn('cores', printed)
