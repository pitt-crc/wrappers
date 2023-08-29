"""Print an account's service unit allocation.

This application is designed to interface with the CRC banking application
and will not work without a running bank installation.
"""
import grp
import os
from argparse import Namespace
from typing import Dict

from bank.account_logic import AccountServices

from .utils.cli import BaseParser


class CrcSus(BaseParser):
    """Display the number of service units allocated to an account."""

    def __init__(self) -> None:
        """Define the application commandline interface"""

        super().__init__()
        default_group = grp.getgrgid(os.getgid()).gr_name
        help_text = f"SLURM account name [defaults to your primary group: {default_group}]"
        self.add_argument('account', nargs='?', default=default_group, help=help_text)

    def get_allocation_info(self, account: str) -> Dict[str, int]:
        """Return the service unit allocation for a given account name

        Args:
            account: The name of the account

        Returns:
            A dictionary mapping cluster names to the number of service units
        """

        acct = AccountServices(account)
        allocs = acct._get_active_proposal_allocation_info()

        allocations = dict()
        for cluster in allocs:
            allocations[cluster.cluster_name] = cluster.service_units_total - cluster.service_units_used

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
            if sus > 0:
                out = f' cluster {cluster:>{cluster_name_length}} has {sus:,} SUs remaining'
            else:
                out = f" cluster {cluster:>{cluster_name_length}} is LOCKED due to exceeding usage limits"
            output_lines.append(out)

        return '\n'.join(output_lines)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        account_info = self.get_allocation_info(args.account)
        output_string = self.build_output_string(args.account, **account_info)
        print(output_string)
