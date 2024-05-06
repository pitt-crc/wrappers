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

    def app_logic(self, args: Namespace,auth_header: dict) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

       requests = get_allocation_requests(KEYSTONE_URL, auth_header)
        # Requests have the following format:
        # {'id': 33241, 'title': 'Resource Allocation Request for hban', 'description': 'Migration from CRC Bank',
        # 'submitted': '2024-04-30', 'status': 'AP', 'active': '2024-04-05', 'expire': '2024-04-30', 'group': 1293}


        # Format the account name and end date as an easy-to-read string
        print(f"The active proposal for account {args.account} ends on {request['expire']} ")
