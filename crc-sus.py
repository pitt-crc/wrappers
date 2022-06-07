#!/usr/bin/env python
"""Print an account's service unit allocation"""

import dataset

from _base_parser import BaseParser, CommonSettings


class CrcSus(BaseParser, CommonSettings):
    """Command line application for printing an account's service unit allocation"""

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcSus, self).__init__()
        self.add_argument(dest='account', type=str, help="the Slurm account")

    def get_allocation_info(self, account):
        """Return the service unit allocation for a given account name

        Args:
            account: The name of the account

        Returns:
            A dictionary mapping cluster names to the number of service units
        """

        # Connect to the database and get the table with proposal service units
        database = dataset.connect(self.banking_db_path)
        table = database['proposal']

        # Ensure a proposal exists for the given account
        db_record = table.find_one(account=account)
        if db_record is None:
            self.error('ERROR: No proposal for the given account was found')

        allocations = {cluster: db_record[cluster] for cluster in self.cluster_partitions}
        return allocations

    @staticmethod
    def build_output_string(account, **allocation):
        """Build a string describing an account's service unit allocation

        Args:
            account: The name of the account
            allocation: The number of service units allocated for each cluster

        Returns:
            A string summarizing the account allocation
        """

        # Convert cluster SUs to strings
        sus_string = ['cluster {} has {} SUs'.format(cluster, sus) for cluster, sus in allocation.items()]

        # Build return string
        string_prefix = 'Account {}'.format(account)
        string_postfix = '\n '.join(sus_string)
        return '\n'.join((string_prefix, string_postfix))

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        account_info = self.get_allocation_info(args.account)
        output_string = self.build_output_string(args.account, **account_info)
        print(output_string)


if __name__ == '__main__':
    CrcSus().execute()
