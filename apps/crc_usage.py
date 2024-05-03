"""User facing application for returning user system usage from the Keystone application.

This application is designed to interface with keystone
and will not work without the application running on keystone.crc.pitt.edu.
"""

import grp
import os
from argparse import Namespace
from getpass import getpass
from datetime import date

from prettytable import PrettyTable
from .utils.keystone import get_auth_header, get_allocations_all, get_allocation_requests, CLUSTERS, KEYSTONE_URL
from .utils.cli import BaseParser
from .utils.system_info import Shell


class CrcUsage(BaseParser):
    """Display a Slurm account's allocation usage"""

    def __init__(self) -> None:
        """Define the application commandline interface"""

        super().__init__()

        default_group = grp.getgrgid(os.getgid()).gr_name
        help_text = "slurm account name (defaults to the current user's primary group name)"
        self.add_argument('account', nargs='?', default=default_group, help=help_text)

    @staticmethod
    def build_usage_table(account_name: str) -> PrettyTable:
        """Build a human-readable usage table for the slurm account with info from Keystone and sreport"""

        auth_header = get_auth_header(KEYSTONE_URL,
                           {'username': os.environ["USER"],
                                      'password': getpass("Please enter your CRC login password:\n")})

        output_table = PrettyTable(header=False, padding_width=5)

        requests = get_allocation_requests(KEYSTONE_URL, auth_header)
        # Requests have the following format:
        # {'id': 33241, 'title': 'Resource Allocation Request for hban', 'description': 'Migration from CRC Bank',
        # 'submitted': '2024-04-30', 'status': 'AP', 'active': '2024-04-05', 'expire': '2024-04-30', 'group': 1293}

        allocations = get_allocations_all(KEYSTONE_URL, auth_header)
        # allocations have the following format:
        # {'id': 111135, 'requested': 50000, 'awarded': 50000, 'final': None, 'cluster': 1, 'request': 33241}

        output_table.title = f"{account_name} Resource Allocation Information"
        #TODO: sources with end dates, filter down to active requests

        output_table.add_row("The following Allocations are contributing towards your group's total:")
        for request in [request for request in requests if request['active'] <= date.today() and request['expire'] > date.today()]:
            output_table.add_row("ID", "TITLE", "EXPIRATION DATE")
            output_table.add_row(f"{request['id']}", f"{request['title']}", f"{request['expire']}")
            output_table.add_row("","CLUSTER","SERVICE UNITS")
            for allocation in [allocation for allocation in allocations if allocation['request'] == request['id']]:
                output_table.add_row("", f"{allocation['awarded']}", f"{CLUSTERS[allocation['cluster']]}")

        # TODO: usage per user from sreport relative to start of earliest active allocation
        # TODO: total usage relative to limit raw
        # TODO: total usage relative to limit percentage

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        account_exists = Shell.run_command(f'sacctmgr -n list account account={args.account} format=account%30')
        if not account_exists:
            raise RuntimeError(f"No slurm account was found with the name '{args.account}'.")

        print(self.build_usage_table(args.account))
