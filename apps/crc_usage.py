"""User facing application for returning user system usage from the CRC banking application.

This application is designed to interface with the CRC banking application
and will not work without a running bank installation.
"""

import grp
import os
from argparse import Namespace

from .utils.cli import CommandlineApplication, Parser
from .utils.system_info import Shell


class CrcUsage(CommandlineApplication):
    """Display a Slurm account's cluster usage."""

    banking_executable = '/ihome/crc/bank/crc_bank.py usage'

    def app_interface(self, parser: Parser) -> None:
        """Define the application commandline interface"""

        default_group = grp.getgrgid(os.getgid()).gr_name
        help_text = "slurm account name (defaults to the current user's primary group name)"
        parser.add_argument('account', nargs='?', default=default_group, help=help_text)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        account_exists = Shell.run_command(f'sacctmgr -n list account account={args.account} format=account%30')
        if not account_exists:
            raise RuntimeError(f"No slurm account was found with the name '{args.account}'.")

        print(Shell.run_command(f'{self.banking_executable} {args.account}'))
