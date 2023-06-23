"""Print the end date for an account's proposal.

This application is designed to interface with the CRC banking application
and will not work without a running bank installation.
"""

from argparse import Namespace
from datetime import datetime

import sqlalchemy as sa

from .utils.cli import BaseParser
from .utils.system_info import Shell


class CrcProposalEnd(BaseParser):
    """Display the end date for an account's current CRC proposal."""

    banking_db_path = 'sqlite:////ihome/crc/bank/crc_bank.db'

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcProposalEnd, self).__init__()

        default_group = Shell.run_command("id -gn")
        self.add_argument(
            'account', default=default_group, nargs='?',
            help=f'the name of the Slurm account [default: {default_group}]')

    def get_proposal_end_date(self, account: str) -> datetime:
        """Get the proposal end date for a given account

        Args:
            account: The name of the account

        Returns:
            The proposal end date as a ``datetime`` object
        """
        
        # Connect to the database and get the table with proposal service units
        engine = sa.create_engine(self.banking_db_path)
        connection = engine.connect()
        
        # Ensure a proposal exists for the given account
        account_id = connection.execute(sa.text("SELECT id FROM account where account.name == 'test'")).scalars().first()

        proposals = connection.execute(sa.text(f"SELECT * FROM proposal where proposal.account_id = {account_id}")).all()

        if proposals is None:
            raise ValueError('ERROR: No proposal for the given account was found')

        return proposals[-1].end_date

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        end_date = self.get_proposal_end_date(args.account)

        # Format the account name and end date as an easy-to-read string
        print(f"Proposal ends on {end_date} for account {args.account} on H2P")
