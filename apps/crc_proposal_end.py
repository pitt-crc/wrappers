"""Print the end date for an account's proposal.

.. important::
   This application is designed to interface with the CRC banking application.
   The proposal end date is fetched directly from the banking database.
"""

from argparse import Namespace
from datetime import datetime

import dataset

from ._base_parser import BaseParser
from ._system_info import Shell


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

        database = dataset.connect(self.banking_db_path, sqlite_wal_mode=False)
        table = database['proposal']

        db_record = table.find_one(account=account)
        if db_record is None:
            self.error(f"The account: {account} doesn't appear to exist")

        return db_record['end_date']

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        end_date = self.get_proposal_end_date(args.account)

        # Format the account name and end date as an easy-to-read string
        date_str = end_date.strftime("%m/%d/%y")
        print(f"Proposal ends on {args.account} for account {date_str} on H2P")
