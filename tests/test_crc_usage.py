"""Tests for the ``CrcUsage`` class."""

import os
from unittest import TestCase, skipIf

import grp

from apps.crc_usage import CrcUsage
from apps.utils.system_info import Slurm


class AccountArgument(TestCase):
    """Test parsing of the ``account`` argument"""

    def test_default_account(self) -> None:
        """Test the default account matches the current user's primary group"""

        app_parser = CrcUsage().parser
        parsed_account = app_parser.parse_args([]).account
        current_account = grp.getgrgid(os.getgid()).gr_name
        self.assertEqual(current_account, parsed_account)

    def test_custom_account_name(self) -> None:
        """Test a custom account is used when specified"""

        app_parser = CrcUsage().parser
        parsed_account = app_parser.parse_args(['dummy_account']).account
        self.assertEqual('dummy_account', parsed_account)


@skipIf(not Slurm.is_installed(), 'Slurm is required to run this test')
class MissingAccountError(TestCase):
    """Test error handling when an account does not exist"""

    def test_error_on_fake_account(self) -> None:
        """Test a ``RuntimeError`` is raised for a missing slurm account"""

        app = CrcUsage()
        args = app.parser.parse_args(['dummy_account'])

        with self.assertRaisesRegex(RuntimeError, 'No slurm account was found'):
            app.app_logic(args)
