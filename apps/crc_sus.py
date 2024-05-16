"""Print an account's service unit allocation, with a usage value relative to that amount.

This application is designed to interface with the Keystone banking system
and will not work without a running keystone installation.
"""

import grp
import os
from argparse import Namespace
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
        keystone_group_id = get_researchgroup_id(KEYSTONE_URL, args.account, auth_header)
        alloc_requests = get_active_requests(KEYSTONE_URL, keystone_group_id, auth_header)
        if not alloc_requests:
            print(f"No active allocation information found in accounting system for '{args.account}'")
            print("Showing SUs for most recently expired Resource Allocation Request:")
            alloc_requests = get_most_recent_expired_request(KEYSTONE_URL, keystone_group_id, auth_header)

        per_cluster_totals = get_per_cluster_totals(alloc_requests, auth_header)
        earliest_date = get_earliest_startdate(alloc_requests)

        for cluster in per_cluster_totals:
            used = Slurm.get_cluster_usage_by_user(args.account, earliest_date, cluster)
            if not used:
                used = 0
            else:
                used = int(used['total'])

            print(self.build_output_string(args.account, used, per_cluster_totals[cluster], cluster))
