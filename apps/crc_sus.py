"""Print an account's service unit allocation"""

from argparse import Namespace
from typing import Dict

import dataset

from ._base_parser import BaseParser
from ._system_info import Shell, SlurmInfo


class CrcSus(BaseParser):
    """Display the number of service units allocated to an account."""

    banking_db_path = 'sqlite:////ihome/crc/bank/crc_bank.db'

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcSus, self).__init__()

        default_group = Shell.run_command("id -gn")
        help_text = f'slurm account name [default: {default_group}]'
        self.add_argument('account', nargs='?', default=default_group, help=help_text)

    def get_allocation_info(self, account: str) -> Dict[str, int]:
        """Return the service unit allocation for a given account name

        Args:
            account: The name of the account

        Returns:
            A dictionary mapping cluster names to the number of service units
        """

        # Connect to the database and get the table with proposal service units
        database = dataset.connect(self.banking_db_path)
        table = database['proposal']

        # Ensure a proposal exists for the given account
        db_record = table.find_one(account=account)
        if db_record is None:
            self.error('ERROR: No proposal for the given account was found')

        allocations = dict()
        for cluster in SlurmInfo.get_cluster_names():
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

        output_lines = ['Account {}'.format(account)]
        cluster_name_length = max(len(cluster) for cluster in allocation)

        for cluster, sus in allocation.items():
            cluster_name = cluster.rjust(cluster_name_length)
            output_lines.append(' cluster {} has {:,} SUs'.format(cluster_name, sus))

        return '\n'.join(output_lines)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        account_info = self.get_allocation_info(args.account)
        output_string = self.build_output_string(args.account, **account_info)
        print(output_string)
