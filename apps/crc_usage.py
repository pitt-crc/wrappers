"""User facing application for returning user system usage from the Keystone application.

This application is designed to interface with keystone
and will not work without the application running on keystone.crc.pitt.edu.
"""

import grp
import os
from argparse import Namespace
from getpass import getpass

from prettytable import PrettyTable

from keystone_client import KeystoneClient
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
    def print_summary_table(alloc_requests: [dict], account_name: str, per_request_totals: dict) -> None:
        """Build and print a human-readable summary table for the slurm account with info from Keystone"""

        # Initialize table for summary of requests and allocations
        summary_table = PrettyTable(header=True, padding_width=2, max_table_width=79, min_table_width=79)
        summary_table.title = f"Resource Allocation Request Information for '{account_name}'"
        summary_table.field_names = ["ID", "TITLE", "EXPIRATION DATE"]

        # Print request and allocation information for active allocations from the provided group
        for request in alloc_requests:

            summary_table.add_row([f"{request['id']}", f"{request['title']}", f"{request['expire']}"], divider=True)
            summary_table.add_row(["", "CLUSTER", "SERVICE UNITS"])
            summary_table.add_row(["", "----", "----"])
            awarded_totals = per_request_totals[request['id']]

            for cluster, total in awarded_totals.items():
                summary_table.add_row(["", f"{cluster}", f"{total}"])

            summary_table.add_row(["", "", ""], divider=True)

        print(summary_table)

    @staticmethod
    def print_usage_table(account_name: str, awarded_totals: dict, earliest_date: date) -> None:
        """Build and print a human-readable usage table for the slurm account with info from Keystone and
        sreport"""

        # Initialize table for summary of usage
        usage_table = PrettyTable(header=False, padding_width=2, max_table_width=79, min_table_width=79)
        usage_table.title = f"Summary of Usage Across All Clusters"

        for cluster, total_awarded in awarded_totals.items():
            usage_by_user = Slurm.get_cluster_usage_by_user(account_name=account_name,
                                                            start_date=earliest_date,
                                                            cluster=cluster)
            if not usage_by_user:
                usage_table.add_row([f"{cluster}", f"TOTAL USED: 0", f"AWARDED: {total_awarded}", f"% USED: 0"],
                                    divider=True)
                usage_table.add_row(["", "", "", ""], divider=True)
                continue

            total_used = int(usage_by_user.pop('total'))
            percent_used = int((total_used / total_awarded * 100) // 1)
            usage_table.add_row(
                [f"{cluster}", f"TOTAL USED: {total_used}", f"AWARDED: {total_awarded}", f"% USED: {percent_used}"],
                divider=True)
            usage_table.add_row(["", "USER", "USED", "% USED"])
            usage_table.add_row(["", "----", "----", "----"])
            for user, usage in sorted(usage_by_user.items(), key=lambda item: item[1], reverse=True):
                percent = int((usage / total_awarded * 100) // 1)
                if percent == 0:
                    percent = '<1'
                usage_table.add_row(["", user, int(usage), percent])

            usage_table.add_row(["", "", "", ""], divider=True)

        print(usage_table)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        Slurm.check_slurm_account_exists(account_name=args.account)
        keystone_session = KeystoneClient(url=KEYSTONE_URL)
        keystone_session.login(username=os.environ["USER"], password=getpass("Please enter your CRC login password:\n"))

        # Gather AllocationRequests from Keystone
        group_id = get_team_id(keystone_session, args.account)
        alloc_requests = get_active_requests(keystone_session, group_id)

        if not alloc_requests:
            print(f"\033[91m\033[1mNo active allocation information found in accounting system for '{args.account}'!\n")
            print("Showing usage information for most recently expired Resource Allocation Request: \033[0m")
            alloc_requests = [get_most_recent_expired_request(keystone_session, group_id)]

        clusters = get_enabled_cluster_ids(keystone_session)

        self.print_summary_table(alloc_requests,
                                 args.account,
                                 get_per_cluster_totals(keystone_session, alloc_requests, clusters, per_request=True))

        self.print_usage_table(args.account,
                               get_per_cluster_totals(keystone_session, alloc_requests, clusters),
                               get_earliest_startdate(alloc_requests))
