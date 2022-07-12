"""Command line interface that wraps the banking application

Command Line Interface
----------------------

.. argparse::
   :nodescription:
   :module: apps.crc_usage
   :func: CrcUsage
   :prog: crc-usage
"""

from ._base_parser import BaseParser
from ._system_info import Shell


class CrcUsage(BaseParser):
    """Display a Slurm account's cluster usage."""

    banking_executable = '/ihome/crc/bank/crc_bank.py usage'

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcUsage, self).__init__()

        default_group = Shell.run_command("id -gn")
        help_text = f'slurm account name [default: {default_group}]'
        self.add_argument('account', nargs='?', default=default_group, help=help_text)

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        account_exists = Shell.run_command('sacctmgr -n list account account={} format=account%30'.format(args.account))
        if not account_exists:
            self.error("The group '{}' doesn't have an account according to Slurm".format(args.account))

        bank_info_command = '{} {}'.format(self.banking_executable, args.account)
        print(Shell.run_command(bank_info_command))
