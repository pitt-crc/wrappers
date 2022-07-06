"""Tests for the ``crc-scontrol`` application."""

from unittest import TestCase

from _utils import SlurmInfo

CrcShowConfig = __import__('crc-show-config').CrcShowConfig


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_clusters_are_valid_args(self):
        """Test clusters defined in common settings are valid values for the ``--cluster`` argument"""

        app = CrcShowConfig()

        for cluster in SlurmInfo.get_cluster_names():
            known_args, unknown_args = app.parse_known_args(['--cluster', cluster])
            self.assertEqual(cluster, known_args.cluster)
            self.assertFalse(unknown_args)
