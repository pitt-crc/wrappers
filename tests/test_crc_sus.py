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


class OutputStringFormatting(TestCase):
    """Test the formatting of the output string"""

    def test_output_matches_manual_string(self):
        """Compare output string from the app with manually constructed expectation"""

        output_string = CrcSus.build_output_string(account='sam', smp=10, htc=20)
        expected_string = (
            'Account sam\n'
            ' cluster smp has 10 SUs\n'
            ' cluster htc has 20 SUs'
        )

        self.assertEqual(expected_string, output_string)
