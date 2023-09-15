"""Tests for the ``crc-interactive`` application."""

import unittest
from argparse import ArgumentTypeError
from datetime import time
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


class TestParseTime(unittest.TestCase):
    """Test the parsing of time strings"""

    def test_valid_time(self) -> None:
        """Test the parsing of valid time strings"""

        self.assertEqual(CrcInteractive.parse_time('1'), time(1, 0, 0))
        self.assertEqual(CrcInteractive.parse_time('01'), time(1, 0, 0))
        self.assertEqual(CrcInteractive.parse_time('23:59'), time(23, 59, 0))
        self.assertEqual(CrcInteractive.parse_time('12:34:56'), time(12, 34, 56))

    def test_invalid_time_format(self) -> None:
        """Test an errr is raised for invalid time formatting"""

        # Test with invalid time formats
        with self.assertRaises(ArgumentTypeError, msg='Error not raised for invalid delimiter'):
            CrcInteractive.parse_time('12-34-56')

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for too many digits'):
            CrcInteractive.parse_time('123:456:789')

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for too many segments'):
            CrcInteractive.parse_time('12:34:56:78')

    def test_invalid_time_value(self) -> None:
        """Test an errr is raised for invalid time values"""

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for invalid hour'):
            CrcInteractive.parse_time('25:00:00')

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for invalid minute'):
            CrcInteractive.parse_time('12:60:00')

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for invalid second'):
            CrcInteractive.parse_time('12:34:60')

    def test_empty_string(self) -> None:
        """Test an error is raised for empty strings"""

        with self.assertRaises(ArgumentTypeError):
            CrcInteractive.parse_time('')
