"""Tests for the ``crc-squeue`` application."""

from unittest import TestCase

CrcSus = __import__('crc-squeue').CrcSus


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_default_flags_are_false(self):
        raise NotImplementedError


class SlurmCommandCreation(TestCase):
    """Test the creation of ``squeue`` commands based on command line arguments"""

    def test_format_matches_args(self):
        raise NotImplementedError

    def test_watch_option_adds_flag(self):
        raise NotImplementedError

    def test_all_option_adds_flag(self):
        raise NotImplementedError
