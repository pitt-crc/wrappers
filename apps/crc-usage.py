"""Command line interface that wraps the banking application"""

from ._base_parser import BaseParser
from ._utils import Shell


class CrcUsage(BaseParser):
    """Command line application for printing a slurm account's cluster usage"""

    banking_executable = '/ihome/crc/bank/crc_bank.py usage'

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcUsage, self).__init__()

        default_group = Shell.run_command("id -gn")
        self.add_argument('account', default=default_group, nargs='?', help='slurm account name')

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


if __name__ == '__main__':
    CrcUsage().execute()
