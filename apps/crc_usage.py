"""Command line application for displaying allocation usage for a Slurm account.

The `crc-usage` application queries both Keystone and Slurm to produce a
summary of awarded service units and per-user consumption across all clusters
in an account's active allocation.
"""

import grp
import os
from argparse import Namespace
from getpass import getpass

from prettytable import PrettyTable

from .utils.cli import BaseParser
from .utils.keystone import (
    authenticate_keystone_session,
    get_active_requests,
    get_earliest_startdate,
    get_enabled_cluster_ids,
    get_most_recent_expired_request,
    get_per_cluster_totals,
    KEYSTONE_URL)
from .utils.system_info import Slurm


class CrcUsage(BaseParser):
    """Display allocation and usage summaries for a Slurm account."""

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super().__init__()

        default_group = grp.getgrgid(os.getgid()).gr_name

        self.add_argument(
            'account', nargs='?', default=default_group,
            help="Slurm account name (defaults to the current user's primary group name)")

    @staticmethod
    def print_summary_table(alloc_requests: list[dict], account_name: str, per_request_totals: dict) -> None:
        """Print a table summarizing active allocation requests and their awarded service units.

        Args:
            alloc_requests: A list of active allocation request records.
            account_name: The name of the Slurm account.
            per_request_totals: Awarded service unit totals keyed by request ID and cluster name.
        """

        # Print request and allocation information for active allocations from the provided group
        table = PrettyTable(header=True, padding_width=2, max_table_width=79, min_table_width=79)
        table.title = f"Resource Allocation Request Information for '{account_name}'"
        table.field_names = ['ID', 'TITLE', 'EXPIRATION DATE']

        for request in alloc_requests:
            table.add_row([request['id'], request['title'], request['expire']], divider=True)
            table.add_row(['', 'CLUSTER', 'SERVICE UNITS'])
            table.add_row(['', '----', '----'])

            for cluster, total in per_request_totals[request['id']].items():
                table.add_row(['', cluster, total])

            table.add_row(['', '', ''], divider=True)

        print(table)

    @staticmethod
    def print_usage_table(account_name: str, awarded_totals: dict, earliest_date) -> None:
        """Print a table summarizing per-user service unit consumption across all clusters.

        Args:
            account_name: The name of the Slurm account.
            awarded_totals: Total awarded service units keyed by cluster name.
            earliest_date: The start date to use when querying usage from Slurm.
        """

        table = PrettyTable(header=False, padding_width=2, max_table_width=79, min_table_width=79)
        table.title = 'Summary of Usage Across All Clusters'

        for cluster, total_awarded in awarded_totals.items():
            usage_by_user = Slurm.get_cluster_usage_by_user(account_name, earliest_date, cluster)

            if not usage_by_user:
                table.add_row([cluster, 'TOTAL USED: 0', f'AWARDED: {total_awarded}', '% USED: 0'], divider=True)
                table.add_row(['', '', '', ''], divider=True)
                continue

            total_used = int(usage_by_user.pop('total'))
            percent_used = int(total_used / total_awarded * 100 // 1)
            table.add_row([cluster, f'TOTAL USED: {total_used}', f'AWARDED: {total_awarded}', f'% USED: {percent_used}'], divider=True)
            table.add_row(['', 'USER', 'USED', '% USED'])
            table.add_row(['', '----', '----', '----'])

            for user, usage in sorted(usage_by_user.items(), key=lambda item: item[1], reverse=True):
                percent = int(usage / total_awarded * 100 // 1) or '<1'
                table.add_row(['', user, int(usage), percent])

            table.add_row(['', '', '', ''], divider=True)

        print(table)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application.

        Args:
            args: Parsed command line arguments.
        """

        Slurm.check_slurm_account_exists(account_name=args.account)

        session = authenticate_keystone_session(
            username=os.environ['USER'],
            password=getpass('Please enter your CRCD login password:\n')
        )

        alloc_requests = get_active_requests(session, args.account)

        if not alloc_requests:
            try:
                alloc_requests = [
                    get_most_recent_expired_request(session, args.account)
                ]

                print(f'\033[91m\033[1mNo active allocation information found in accounting system for \'{args.account}\'!\n')
                print('Attempting to show the most recently expired Resource Allocation Request info:\033[0m \n')

            except IndexError:
                print(
                    '\033[91m\033[1mNo allocation information found. Either the group does not have any allocations, '
                    'or you do not have permissions to view them. If you believe this to be a mistake, please submit '
                    'a help ticket to the CRCD team.\033[0m \n'
                )

                exit()

        clusters = get_enabled_cluster_ids(session)

        self.print_summary_table(
            alloc_requests, args.account,
            get_per_cluster_totals(session, alloc_requests, clusters, per_request=True))

        self.print_usage_table(
            args.account,
            get_per_cluster_totals(session, alloc_requests, clusters),
            get_earliest_startdate(alloc_requests))
