"""Tests for the ``CrcUsage`` class."""

import grp
import os
from unittest import TestCase, skipIf

from apps.crc_usage import CrcUsage
from apps.utils.system_info import Slurm


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_default_account(self) -> None:
        """Test the default account matches the current user's primary group"""

        parsed_account = CrcUsage().parse_args([]).account
        current_account = grp.getgrgid(os.getgid()).gr_name
        self.assertEqual(current_account, parsed_account)

    def test_custom_account_name(self) -> None:
        """Test a custom account is used when specified"""

        parsed_account = CrcUsage().parse_args(['dummy_account']).account
        self.assertEqual('dummy_account', parsed_account)


@skipIf(not Slurm.is_installed(), 'Slurm is required to run this test')
class MissingAccountError(TestCase):
    """Test error handling when an account does not exist"""

    def test_error_on_fake_account(self) -> None:
        """Test a ``RuntimeError`` is raised for a missing slurm account"""

        app = CrcUsage()
        args = app.parse_args(['dummy_account'])

        with self.assertRaisesRegex(RuntimeError, 'No slurm account was found'):
            app.app_logic(args)
