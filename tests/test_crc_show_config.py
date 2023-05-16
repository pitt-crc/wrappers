"""Tests for the ``crc-scontrol`` application."""

from unittest import TestCase

from apps.crc_show_config import CrcShowConfig


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_default_partition_is_none(self) -> None:
        """Test the cluster argument defaults to ``all`` clusters"""

        args, _ = CrcShowConfig().parse_known_args(['-c', 'cluster'])
        self.assertIsNone(args.partition)

    def test_print_defaults_to_false(self) -> None:
        """Test the ``prin-command`` option is disabled by default"""

        args, _ = CrcShowConfig().parse_known_args(['-c', 'cluster'])
        self.assertFalse(args.print_command)
