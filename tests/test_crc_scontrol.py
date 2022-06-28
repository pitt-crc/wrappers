"""Tests for the ``crc-scontrol`` application."""

from unittest import TestCase

from _base_parser import CommonSettings

CrcScontrol = __import__('crc-scontrol').CrcScontrol


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_clusters_are_valid_arguments(self):
        """Test clusters defined in common settings are valid values for the ``--cluster`` argument"""

        app = CrcScontrol()

        for cluster in CommonSettings.cluster_names:
            known_args, unknown_args = app.parse_known_args(['--cluster', cluster])
            self.assertEqual(cluster, known_args.cluster)
            self.assertFalse(unknown_args)
