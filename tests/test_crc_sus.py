"""Tests for the ``crc-sus`` application."""

import grp
import os
from unittest import TestCase

from apps.crc_sus import CrcSus


class AccountArgument(TestCase):
    """Test parsing of the ``account`` argument"""

    def test_default_account(self) -> None:
        """Test the default account matches the current user's primary group"""

        parsed_account = CrcSus().parse_args([]).account
        current_account = grp.getgrgid(os.getgid()).gr_name
        self.assertEqual(current_account, parsed_account)

    def test_custom_account_name(self) -> None:
        """Test a custom account is used when specified"""

        parsed_account = CrcSus().parse_args(['dummy_account']).account
        self.assertEqual('dummy_account', parsed_account)


class OutputStringFormatting(TestCase):
    """Test the formatting of the output string"""

    def test_output_matches_string(self) -> None:
        """Compare output string from the app with manually constructed expectation"""

        output_string = CrcSus().build_output_string(account='sam', smp=10, htc=20)
        expected_string = (
            'Account sam\n'
            ' cluster smp has 10 SUs\n'
            ' cluster htc has 20 SUs'
        )

        self.assertEqual(expected_string, output_string)
