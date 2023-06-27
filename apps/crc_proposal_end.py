"""Print the end date for an account's proposal.

This application is designed to interface with the CRC banking application
and will not work without a running bank installation.
"""

from argparse import Namespace
from datetime import datetime

from bank.account_logic import AccountServices

from .utils.cli import BaseParser
from .utils.system_info import Shell


class CrcProposalEnd(BaseParser):
    """Display the end date for an account's current CRC proposal."""

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcProposalEnd, self).__init__()
        default_group = Shell.run_command("id -gn")
        help_text = f"SLURM account name [defaults to your primary group: {default_group}]"
        self.add_argument('account', nargs='?', default=default_group, help=help_text)

    def get_proposal_end_date(self, account: str) -> str:
        """Get the proposal end date for a given account

        Args:
            account: The name of the account

        Returns:
            The proposal end date in string format
        """

        acct = AccountServices(account)
        return acct._get_active_proposal_end_date()

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        end_date = self.get_proposal_end_date(args.account)

        # Format the account name and end date as an easy-to-read string
        print(f"The active proposal for account {args.account} ends on {end_date}")
