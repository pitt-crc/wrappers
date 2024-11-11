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
        keystone_session = KeystoneClient(url=KEYSTONE_URL)
        keystone_session.login(username=os.environ["USER"], password=getpass("Please enter your CRC login password:\n"))

        team_id = get_team_id(keystone_session, args.account)
        alloc_requests = get_active_requests(keystone_session, team_id)

        if not alloc_requests:
            print(f"\033[91m\033[1mNo active allocation information found in accounting system for '{args.account}'!\n")
            print("Showing end date for most recently expired Resource Allocation Request:\033[0m \n")
            try:
                alloc_requests = [get_most_recent_expired_request(keystone_session, team_id)]
            except IndexError:
                print("\033[91m\033[1mNo allocation information found. Either the group does not have any allocations, or you do not have permissions to view them. If you believe this to be a mistake, please submit a help ticket to the CRCD team. \033[0m \n")
                exit()

        for request in alloc_requests:
            print(f"'{request['title']}' ends on {request['expire']} ")
