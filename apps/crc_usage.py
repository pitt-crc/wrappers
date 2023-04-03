"""User facing application for returning user system usage from the CRC banking application.

This application is designed to interface with the CRC banking application
and will not work without a running bank installation.
"""

from argparse import Namespace

from ._base_parser import BaseParser
from ._system_info import Shell


class CrcUsage(BaseParser):
    """Display a Slurm account's cluster usage."""

    banking_executable = '/ihome/crc/bank/crc_bank.py usage'

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcUsage, self).__init__()

        default_group = Shell.run_command("id -gn")
        help_text = f'slurm account name [default: {default_group}]'
        self.add_argument('account', nargs='?', default=default_group, help=help_text)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        account_exists = Shell.run_command(f'sacctmgr -n list account account={args.account} format=account%30')
        if not account_exists:
            self.error(f"The group '{args.account}' doesn't have an account according to Slurm")

        print(Shell.run_command(f'{self.banking_executable} {args.account}'))
