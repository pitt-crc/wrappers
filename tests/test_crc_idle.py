"""Tests for the ``crc-idle`` application"""

from unittest import TestCase, skip

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

    @skip('Requires slurm utilities')
    def test_clusters_default_to_false(self) -> None:
        """Test all cluster flags default to a ``False`` value"""

        app = CrcIdle()
        args, unknown_args = app.parse_known_args([])

        self.assertFalse(unknown_args)
        for cluster in Slurm.get_cluster_names():
            self.assertFalse(getattr(args, cluster))


class ClusterList(TestCase):
    """Test the selection of what clusters to print"""

    @skip('Requires slurm utilities')
    def test_defaults_all_clusters(self) -> None:
        """Test all clusters are returned if none are specified in the parsed arguments"""

        app = CrcIdle()
        args, unknown_args = app.parse_known_args(['-p', 'partition1'])
        self.assertFalse(unknown_args)

        returned_clusters = app.get_cluster_list(args)
        self.assertCountEqual(Slurm.get_cluster_names(), returned_clusters)

    def test_returns_arg_values(self) -> None:
        """Test returned cluster names match the clusters specified in the parsed arguments"""
        app = CrcIdle()
        args, unknown_args = app.parse_known_args(['-s', '--mpi'])
        self.assertFalse(unknown_args)

        returned_clusters = app.get_cluster_list(args)
        self.assertCountEqual(['smp', 'mpi'], returned_clusters)
