"""A simple wrapper around the Slurm ``squeue`` command."""

import getpass
from argparse import Namespace
from datetime import datetime, date
from time import sleep

from .utils.keystone import *
from .utils.system_info import Slurm
from .utils.cli import BaseParser


class CrcSqueue(BaseParser):
    """Summarize currently running Slurm jobs."""

    # Formats for output data depending on user provided arguments
    output_format_user = "-o '%.8i %.3P %.35j %.2t %.12M %.6D %.4C %.50R %.20S'"
    output_format_all = "-o '%.8i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.50R %.20S'"

    def __init__(self) -> None:
        """Define the application commandline interface"""

        super(CrcSqueue, self).__init__()
        self.add_argument('-a', '--all', action='store_true', help='show all jobs (defaults to current user only)')
        self.add_argument('-c', '--cluster', nargs='?', default='all', help='only show jobs for the given cluster')
        self.add_argument('-w', '--watch', action='store_const', const=10, help='update information every 10 seconds')
        self.add_argument('-z', '--print-command', action='store_true',
                          help='print the equivalent slurm command and exit')

    @classmethod
    def build_slurm_command(cls, args: Namespace) -> str:
        """Return an ``squeue`` command matching parsed command line arguments

        Args:
            args: Parsed command line arguments
        """

        # Build the base command
        command_options = [f'squeue -M {args.cluster}']

        if args.all:
            command_options.append(cls.output_format_all)

        else:
            user = f'-u {getpass.getuser()}'
            command_options.append(user)
            command_options.append(cls.output_format_user)

        return ' '.join(command_options)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """
        
        Slurm.check_slurm_account_exists(args.account)
        
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
           # Check if proposal will expire within 30 days. If yes, print a message to inform the user
           if (date.fromisoformat(request['expire'])-date.today()).days<30 
                print(f"The active proposal for account {args.account} will expire soon on {request['expire']}. Please begin working on a new proposal if you want to run jobs beyond that date.")
      
        
        command = self.build_slurm_command(args)
        if args.print_command:
            print(command)
            return

        print(Shell.run_command(command))
        while args.watch:
            sleep(args.watch)
            print('\n', Shell.run_command(command))
