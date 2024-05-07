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

        # Right justify cluster names to the same length
        sus = total-used
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

        account_exists = Shell.run_command()
        check_slurm_account_exists(args.account)

        if not account_exists:
            raise RuntimeError(f"No Slurm account was found with the name '{args.account}'.")

        auth_header = get_auth_header(KEYSTONE_URL,
                                      {'username': os.environ["USER"],
                                       'password': getpass("Please enter your CRC login password:\n")})
        requests = get_allocation_requests(KEYSTONE_URL, auth_header)


        for request in requests:
            for allocation in [allocation for allocation in allocations if allocation['request'] == request['id']]:
                cluster = CLUSTERS[allocation['cluster']]
                awarded = allocation['awarded']
                used = Shell.run_command(f'sreport cluster AccountUtilizationByUser -n -T billing -t hours cluster={cluster} accounts={args.account} users={args.user} start={request['active']} end={request['expire']} format=Used')
                per_cluster_totals.setdefault(cluster, 0)
                per_cluster_totals[cluster] += awarded
                output_string = self.build_output_string(args.account, used,per_cluster_totals[cluster])
                print(output_string)
