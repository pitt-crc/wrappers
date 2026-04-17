"""Command line application for displaying service unit balances for a Slurm account.

The `crc-sus` application queries both Keystone and Slurm to report how many
service units have been used and how many remain for each cluster in an account's
active allocation.
"""

import grp
import os
from argparse import Namespace
from getpass import getpass

from .utils.cli import BaseParser
from .utils.keystone import (
    authenticate_keystone_session,
    get_active_requests,
    get_earliest_startdate,
    get_enabled_cluster_ids,
    get_most_recent_expired_request,
    get_per_cluster_totals)
from .utils.system_info import Slurm


class CrcSus(BaseParser):
    """Display the service unit balance for a Slurm account."""

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super().__init__()

        default_group = grp.getgrgid(os.getgid()).gr_name

        self.add_argument(
            'account', nargs='?', default=default_group,
            help=f'Slurm account name [defaults to your primary group: {default_group}]')

    @staticmethod
    def build_output_string(account: str, used: int, total: int, cluster: str) -> str:
        """Return a string summarizing service unit usage for one cluster.

        Args:
            account: The name of the Slurm account.
            used: The number of service units consumed on the cluster.
            total: The total number of service units awarded on the cluster.
            cluster: The name of the cluster.

        Returns:
            A formatted string describing remaining or locked status for the cluster.
        """

        remaining = total - used
        if remaining > 0:
            status = f'cluster {cluster} has {remaining} SUs remaining'

        else:
            status = f'cluster {cluster} is LOCKED due to reaching usage limits'

        return f'Account {account}\n {status}'

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
                print('Showing remaining service unit amounts for most recently expired Resource Allocation Request:\033[0m \n')

            except IndexError:
                print(
                    '\033[91m\033[1mNo allocation information found. Either the group does not have any allocations, '
                    'or you do not have permissions to view them. If you believe this to be a mistake, please submit '
                    'a help ticket to the CRCD team.\033[0m \n'
                )

                exit()

        per_cluster_totals = get_per_cluster_totals(session, alloc_requests, get_enabled_cluster_ids(session))
        earliest_date = get_earliest_startdate(alloc_requests)

        for cluster, total in per_cluster_totals.items():
            usage = Slurm.get_cluster_usage_by_user(args.account, earliest_date, cluster)
            used = int(usage['total']) if usage else 0
            print(self.build_output_string(args.account, used, total, cluster))
