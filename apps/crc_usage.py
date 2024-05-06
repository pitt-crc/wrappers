"""User facing application for returning user system usage from the Keystone application.

This application is designed to interface with keystone
and will not work without the application running on keystone.crc.pitt.edu.
"""

import grp
import os
from argparse import Namespace
from getpass import getpass
from datetime import datetime, date

from prettytable import PrettyTable
from .utils.keystone import *
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
    def print_tables(account_name: str, group_id: int, auth_header: dict) -> None:
        """Build and print human-readable summary and usage tables for the slurm account with info from Keystone and
        sreport"""

        # Gather allocations and requests from Keystone
        requests = get_allocation_requests(KEYSTONE_URL, auth_header)
        allocations = get_allocations_all(KEYSTONE_URL, auth_header)

        # Initialize table for summary of requests and allocations
        summary_table = PrettyTable(header=True, padding_width=5)
        summary_table.title = f"Resource Allocation Request Information for {account_name}"
        summary_table.field_names(["ID", "TITLE", "EXPIRATION DATE"])

        # Initialize table for summary of usage
        usage_table = PrettyTable(header=True, padding_width=5)
        usage_table.title = f"Summary of Usage"

        per_cluster_totals = dict()

        # Print request and allocation information for active allocations from the provided group
        for request in requests:
            summary_table.add_row([f"{request['id']}", f"{request['title']}", f"{request['expire']}"])
            summary_table.add_row(["", "CLUSTER", "SERVICE UNITS"])
            for allocation in [allocation for allocation in allocations if allocation['request'] == request['id']]:
                cluster = CLUSTERS[allocation['cluster']]
                awarded = allocation['awarded']
                per_cluster_totals.setdefault(cluster, 0)
                per_cluster_totals[cluster] += awarded
                summary_table.add_row(["", f"{awarded}", f"{cluster}"])

        print(summary_table)
        print(usage_table)
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
            raise RuntimeError(f"No Slurm account was found with the name '{args.account}'.")

        auth_header = get_auth_header(KEYSTONE_URL,
                                      {'username': os.environ["USER"],
                                       'password': getpass("Please enter your CRC login password:\n")})

        # Determine if provided or default account is in Keystone
        accessible_research_groups = get_researchgroups(KEYSTONE_URL, auth_header)
        keystone_group_id = None
        for group in accessible_research_groups:
            if args.account == group['name']:
                keystone_group_id = int(group['id'])

        if not keystone_group_id:
            print(f"No allocation data found in accounting system for '{args.account}'")
            exit()

        self.print_tables(args.account, keystone_group_id, auth_header)
