"""Tests for the ``crc-sus`` application."""

import grp
import os
from unittest import TestCase

from apps.crc_sus import CrcSus


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments."""

    def test_default_account_is_primary_group(self) -> None:
        """Account defaults to the current user's primary group."""

        parsed = CrcSus().parse_args([]).account
        self.assertEqual(grp.getgrgid(os.getgid()).gr_name, parsed)

    def test_custom_account_stored(self) -> None:
        """An explicitly provided account name is stored correctly."""

        parsed = CrcSus().parse_args(['my_account']).account
        self.assertEqual('my_account', parsed)

    def test_unknown_args_empty_for_valid_input(self) -> None:
        args, unknown = CrcSus().parse_known_args(['my_account'])
        self.assertFalse(unknown)


# ---------------------------------------------------------------------------
# build_output_string
# ---------------------------------------------------------------------------

class BuildOutputString(TestCase):
    """Test the service-unit summary string formatting."""

    def test_remaining_sus_message(self) -> None:
        """Shows 'X SUs remaining' when usage is below the total."""

        result = CrcSus.build_output_string(account='mygroup', used=100, total=1000, cluster='smp')
        self.assertIn('900 SUs remaining', result)
        self.assertIn('mygroup', result)
        self.assertIn('smp', result)

    def test_locked_message_when_over_limit(self) -> None:
        """Shows 'LOCKED' when used equals or exceeds the total."""

        result = CrcSus.build_output_string(account='mygroup', used=1000, total=1000, cluster='smp')
        self.assertIn('LOCKED', result)

    def test_locked_message_when_over_by_one(self) -> None:
        """Shows 'LOCKED' when used exceeds total by one."""

        result = CrcSus.build_output_string(account='mygroup', used=1001, total=1000, cluster='gpu')
        self.assertIn('LOCKED', result)

    def test_zero_used_shows_full_total(self) -> None:
        """With no usage, the full total is reported as remaining."""

        result = CrcSus.build_output_string(account='sam', used=0, total=10, cluster='SMP')
        expected = 'Account sam\n cluster SMP has 10 SUs remaining'
        self.assertEqual(expected, result)

    def test_account_name_in_output(self) -> None:
        """The account name always appears in the output string."""

        result = CrcSus.build_output_string(account='testgroup', used=0, total=500, cluster='mpi')
        self.assertIn('testgroup', result)

    def test_cluster_name_in_output(self) -> None:
        """The cluster name always appears in the output string."""

        result = CrcSus.build_output_string(account='testgroup', used=0, total=500, cluster='htc')
        self.assertIn('htc', result)

    def test_exact_remaining_calculation(self) -> None:
        """Remaining SUs are exactly total - used."""

        result = CrcSus.build_output_string(account='g', used=300, total=1000, cluster='smp')
        self.assertIn('700 SUs remaining', result)
