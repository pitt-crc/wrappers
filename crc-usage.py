#!/usr/bin/env python
"""Command line interface that wraps the banking application"""

from _base_parser import BaseParser


class CrcUsage(BaseParser):
    """Command line application for printing a slurm account's cluster usage"""

    banking_executable = '/ihome/crc/bank/crc_bank.py usage'

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcUsage, self).__init__()

        default_group = self.run_command("id -gn")
        self.add_argument('account', default=default_group, nargs='?', help='slurm account name')

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        account_exists = self.run_command('sacctmgr -n list account account={} format=account%30'.format(args.account))
        if not account_exists:
            self.error("The group '{}' doesn't have an account according to Slurm".format(args.account))

        bank_info = '{} {}'.format(self.banking_executable, args.account)
        print(self.run_command(bank_info))


if __name__ == '__main__':
    CrcUsage().execute()
