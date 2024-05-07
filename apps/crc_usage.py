"""User facing application for returning user system usage from the Keystone application.

This application is designed to interface with keystone
and will not work without the application running on keystone.crc.pitt.edu.
"""

import grp
import os
from argparse import Namespace
from datetime import date
from getpass import getpass
from prettytable import PrettyTable

from .utils.cli import BaseParser
from .utils.keystone import *
from .utils.system_info import Slurm


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

        # Gather requests from Keystone
        requests = get_allocation_requests(KEYSTONE_URL, group_id, auth_header)
        requests = [request for request in requests if date.fromisoformat(request['active']) <= date.today() < date.fromisoformat(request['expire'])]
        if not requests:
            print("No active Resource Allocation Requests found in the accounting system for '{account_name}'")
            exit()

        # Initialize table for summary of requests and allocations
        summary_table = PrettyTable(header=True, padding_width=5, max_width=80)
        summary_table.title = f"Resource Allocation Request Information for {account_name}"
        summary_table.field_names = ["ID", "TITLE", "EXPIRATION DATE"]

        # Initialize table for summary of usage
        usage_table = PrettyTable(header=False, padding_width=5, max_width=80)
        usage_table.title = f"Summary of Usage across all Clusters"

        per_cluster_awarded_totals = dict()

        earliest_date = date.today()
        # Print request and allocation information for active allocations from the provided group
        for request in requests:
            start = date.fromisoformat(request['active'])
            if start < earliest_date:
                earliest_date = start
            summary_table.add_row([f"{request['id']}", f"{request['title']}", f"{request['expire']}"], divider=True)
            summary_table.add_row(["", "CLUSTER", "SERVICE UNITS"])
            summary_table.add_row(["", "----", "----"])
            for allocation in get_allocations_all(KEYSTONE_URL, request['id'], auth_header):
                cluster = CLUSTERS[allocation['cluster']]
                awarded = allocation['awarded']
                per_cluster_awarded_totals.setdefault(cluster, 0)
                per_cluster_awarded_totals[cluster] += awarded
                summary_table.add_row(["", f"{cluster}", f"{awarded}"])
            summary_table.add_row(["","",""], divider=True)

        print(summary_table)
        for cluster, total_awarded in per_cluster_awarded_totals.items():
            usage_by_user = Slurm.get_cluster_usage_by_user(account_name=account_name, start_date=earliest_date, cluster=cluster)
            if not usage_by_user:
                usage_table.add_row([f"{cluster}", f"TOTAL USED: 0", f"AWARDED: {total_awarded}", f"% USED: 0"], divider=True)
                usage_table.add_row(["","","",""], divider=True)
                continue

            total_used = usage_by_user.pop('total')
            percent_used=int(total_used)//int(total_awarded)*100
            usage_table.add_row([f"{cluster}", f"TOTAL USED: {total_used}", f"AWARDED: {total_awarded}", f"% USED: {percent_used}"], divider=True)
            usage_table.add_row(["","USER","USED","% USED"])
            usage_table.add_row(["","----","----","----"])
            for user, usage in usage_by_user.items():
                percent = int(usage)//int(total_awarded)*100
                if percent == 0:
                    percent = '< 1%'
                usage_table.add_row(["", user, int(usage), percent])

            usage_table.add_row(["","","",""], divider=True)

        print(usage_table)


    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        Slurm.check_slurm_account_exists(account_name=args.account)
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
