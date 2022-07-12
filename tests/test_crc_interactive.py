"""Tests for the ``crc-interactive`` application."""

from unittest import TestCase

from apps.crc_interactive import CrcInteractive


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_args_match_class_settings(self) -> None:
        """Test parsed args default to the values defined as class settings"""

        args, _ = CrcInteractive().parse_known_args(['--mpi'])

        self.assertEqual(CrcInteractive.default_time, args.time)
        self.assertEqual(CrcInteractive.default_cores, args.num_cores)
        self.assertEqual(CrcInteractive.default_mem, args.mem)
        self.assertEqual(CrcInteractive.default_gpus, args.num_gpus)
