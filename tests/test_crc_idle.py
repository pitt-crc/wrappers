"""Tests for the `crc-idle` application"""

from argparse import Namespace
from unittest import TestCase
from unittest.mock import patch

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

    def test_get_cluster_list_no_arguments(self):
        """Test returned values when no clusters are specified."""

        app = CrcIdle()
        args = Namespace(smp=False, gpu=False, mpi=False, invest=False, htc=False, partition=None)
        result = app.get_cluster_list(args)

        expected = tuple(app.cluster_types.keys())
        self.assertEqual(expected, result)

    def test_get_cluster_list_with_cluster_arguments(self):
        """Test returned values when select clusters are specified."""

        app = CrcIdle()
        args = Namespace(smp=True, gpu=False, mpi=True, invest=False, htc=False, partition=None)
        result = app.get_cluster_list(args)

        self.assertEqual(('smp', 'mpi'), result)
