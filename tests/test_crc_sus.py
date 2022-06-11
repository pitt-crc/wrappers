"""Tests for the ``crc-sus`` application."""

from unittest import TestCase

CrcSus = __import__('crc-sus').CrcSus


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_account_name_is_parsed(self):
        """Test the account name is recovered from the command line"""

        account_name = 'sam'
        args, unknown_args = CrcSus().parse_known_args([account_name])

        self.assertFalse(unknown_args)
        self.assertEqual(account_name, args.account)
