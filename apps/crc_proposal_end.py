"""Print the end date for an account's proposal.

This application is designed to interface with the CRC banking application
and will not work without a running bank installation.
"""

import grp
import os
from argparse import Namespace
from .utils.keystone import *

from bank.account_logic import AccountServices

from .utils.cli import BaseParser


class CrcProposalEnd(BaseParser):
    """Display the end date for an account's current CRC proposal."""

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcProposalEnd, self).__init__()
        default_group = grp.getgrgid(os.getgid()).gr_name
        help_text = f"SLURM account name [defaults to your primary group: {default_group}]"
        self.add_argument('account', nargs='?', default=default_group, help=help_text)

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

        accessible_research_groups = get_researchgroups(KEYSTONE_URL, auth_header)
        keystone_group_id = None
        for group in accessible_research_groups:
            if args.account == group['name']:
                keystone_group_id = int(group['id'])

        if not keystone_group_id:
            print(f"No allocation data found in accounting system for '{args.account}'")
            exit()

        requests = get_allocation_requests(KEYSTONE_URL, keystone_group_id, auth_header)
        requests = [request for request in requests if date.fromisoformat(request['active']) <= date.today() < date.fromisoformat(request['expire'])]
        if not requests:
            print(f"No active resource allocation requests found in accounting system for '{args.account}'")
            exit()
        for request in requests:    
              print(f"The active proposal for account {args.account} ends on {request['expire']} ")
        # Requests have the following format:
        # {'id': 33241, 'title': 'Resource Allocation Request for hban', 'description': 'Migration from CRC Bank',
        # 'submitted': '2024-04-30', 'status': 'AP', 'active': '2024-04-05', 'expire': '2024-04-30', 'group': 1293}


        # Format the account name and end date as an easy-to-read string
      
