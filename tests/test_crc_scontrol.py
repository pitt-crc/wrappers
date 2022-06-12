"""Tests for the ``crc-scontrol`` application."""

from unittest import TestCase
from unittest.mock import patch

from _base_parser import CommonSettings

CrcScontrol = __import__('crc-scontrol').CrcScontrol


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_clusters_are_valid_arguments(self):
        """Test clusters defined in common settings are valid values for the ``--cluster`` argument"""

        app = CrcScontrol()

        for cluster in CommonSettings.cluster_partitions:
            known_args, unknown_args = app.parse_known_args(['--cluster', cluster])
            self.assertEqual(cluster, known_args.cluster)
            self.assertFalse(unknown_args)


class AppLogic(TestCase):
    """test the routing of app logic based on command-line arguments"""

    @patch('crc-scontrol.CrcScontrol.print_help')
    def test_help_text_for_cluster_and_partition(self, mock_print_help):
        """Ensure help text is printed when ``--cluster`` and ``--partition`` are specified"""

        app = CrcScontrol()
        args, unknown_args = app.parse_known_args(['--cluster', 'smp', '--partition', 'smp'])
        self.assertFalse(unknown_args)

        app.app_logic(args)
        mock_print_help.assert_called()
