"""Print an account's service unit allocation, with a usage value relative to that amount.

This application is designed to interface with the Keystone banking system
and will not work without a running keystone installation.
"""


import grp
import os
from argparse import Namespace
from datetime import date
from getpass import getpass

from .utils.cli import BaseParser
from .utils.keystone import *
from .utils.system_info import Slurm


class CrcSus(BaseParser):
    """Display the number of service units allocated to an account."""

    def __init__(self) -> None:
        """Define the application commandline interface"""

        super().__init__()
        default_group = grp.getgrgid(os.getgid()).gr_name
        help_text = f"SLURM account name [defaults to your primary group: {default_group}]"
        self.add_argument('account', nargs='?', default=default_group, help=help_text)

    @staticmethod
    def build_output_string(account: str, used: int, total: int, cluster: str) -> str:
        """Build a string describing an account's service unit allocation

        Args:
            account: The name of the account
            total: The number of service units allocated for each cluster
            used: number of SUs used on the cluster
            cluster: name of cluster
        Returns:
            A string summarizing the account allocation
        """

        output_lines = [f'Account {account}']

        remaining = total - used

        if remaining > 0:
            out = f' cluster {cluster} has {remaining} SUs remaining'
        else:
            out = f" cluster {cluster} is LOCKED due to reaching usage limits"
        output_lines.append(out)

        return '\n'.join(output_lines)

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

        requests = get_allocation_requests(KEYSTONE_URL, keystone_group_id, auth_header)
        requests = [request for request in requests
                    if date.fromisoformat(request['active']) <= date.today() < date.fromisoformat(request['expire'])]
        if not requests:
            print(f"No active resource allocation requests found in accounting system for '{args.account}'")
            exit()

        earliest_date = date.today()
        per_cluster_totals = {}
        for request in requests:
            start = date.fromisoformat(request['active'])
            if start < earliest_date:
                earliest_date = start

            for allocation in get_allocations_all(KEYSTONE_URL, request['id'], auth_header):
                cluster = CLUSTERS[allocation['cluster']]
                per_cluster_totals.setdefault(cluster, 0)
                per_cluster_totals[cluster] += allocation['awarded']

        for cluster in per_cluster_totals:
            used = Slurm.get_cluster_usage_by_user(args.account, earliest_date, cluster)
            if not used:
                used = 0
            else:
                used = used['total']

            print(self.build_output_string(args.account, used, per_cluster_totals[cluster], cluster))
