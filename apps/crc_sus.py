"""Print an account's service unit allocation.

This application is designed to interface with the CRC banking application
and will not work without a running bank installation.
"""

import grp
import os
from argparse import Namespace
from typing import Dict

from bank.orm import DBConnection

from .utils.cli import BaseParser
from .utils.system_info import Slurm


class CrcSus(BaseParser):
    """Display the number of service units allocated to an account."""

    banking_db_path = 'sqlite:////ihome/crc/bank/crc_bank.db'

    def __init__(self) -> None:
        """Define the application commandline interface"""

        super().__init__()
        default_group = grp.getgrgid(os.getgid()).gr_name
        help_text = "slurm account name (defaults to the current user's primary group name)"
        self.add_argument('account', nargs='?', default=default_group, help=help_text)

    def get_allocation_info(self, account: str) -> Dict[str, int]:
        """Return the service unit allocation for a given account name

        Args:
            account: The name of the account

        Returns:
            A dictionary mapping cluster names to the number of service units
        """

        # Connect to the database and get the table with proposal service units
        database = DBConnection.configure(self.banking_db_path)
        table = database['proposal']

        # Ensure a proposal exists for the given account
        db_record = table.find_one(account=account)
        if db_record is None:
            raise ValueError('ERROR: No proposal for the given account was found')

        # Convert the DB record into a dictionary
        allocations = dict()
        for cluster in Slurm.get_cluster_names():
            if cluster in db_record:
                allocations[cluster] = db_record[cluster]

        return allocations

    @staticmethod
    def build_output_string(account: str, **allocation: int) -> str:
        """Build a string describing an account's service unit allocation

        Args:
            account: The name of the account
            allocation: The number of service units allocated for each cluster

        Returns:
            A string summarizing the account allocation
        """

        output_lines = [f'Account {account}']

        # Right justify cluster names to the same length
        cluster_name_length = max(len(cluster) for cluster in allocation)
        for cluster, sus in allocation.items():
            output_lines.append(f' cluster {cluster:>{cluster_name_length}} has {sus:,} SUs')

        return '\n'.join(output_lines)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        account_info = self.get_allocation_info(args.account)
        output_string = self.build_output_string(args.account, **account_info)
        print(output_string)
