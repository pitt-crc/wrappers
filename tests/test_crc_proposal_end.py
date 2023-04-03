"""Tests for the ``crc-proposal-end`` application."""

from unittest import TestCase

from apps.crc_proposal_end import CrcProposalEnd


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_account_name_is_parsed(self) -> None:
        """Test the account name is recovered from the command line"""

        account_name = 'sam'
        args, unknown_args = CrcProposalEnd().parse_known_args([account_name])

        self.assertFalse(unknown_args)
        self.assertEqual(account_name, args.account)
