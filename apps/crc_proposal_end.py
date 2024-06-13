"""Print the end date for an account's proposal.

This application is designed to interface with the CRC banking application
and will not work without a running bank installation.
"""

import grp
import os
from argparse import Namespace
from getpass import getpass

from .utils.cli import BaseParser
from .utils.keystone import *
from .utils.system_info import Slurm


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

        Slurm.check_slurm_account_exists(args.account)
        keystone_session = KeystoneApi()
        keystone_session.login(username=os.environ["USER"], password=getpass("Please enter your CRC login password:\n"))

        # Attempt to get the primary key for the ResearchGroup
        try:
            keystone_group_id = keystone_session.get('users/researchgroups/',
                                             {'name': args.account},
                                             'json')[0]['id']
        except IndexError:
            print(f"No Slurm Account found in the accounting system for '{args.account}'. \n"
                  f"Please submit a ticket to the CRC team to ensure your allocation was properly configured")
            exit()

        today = date.today().isoformat()
        alloc_requests = [request for request in keystone_session.get('allocations/requests',
                                                              {'group': keystone_group_id,
                                                               'status': 'AP',
                                                               'active__lte': today,
                                                               'expire__gt': today},
                                                              'json'
                                                              )]

        if not alloc_requests:
            print(f"\033[91m\033[1mNo active allocation information found in accounting system for '{args.account}'!\n")
            print("Showing end date for most recently expired Resource Allocation Request:\033[0m")
            alloc_requests = [keystone_session.get('allocations/requests',
                                           {'group': keystone_group_id,
                                            'status': 'AP',
                                            'ordering': '-expire',
                                            'expire__lte': today},
                                           'json'
                                           )]

        for request in alloc_requests:
            print(f"'{request['title']}' ends on {request['expire']} ")
