#!/usr/bin/env python
"""Print an account's service unit allocation"""

import dataset

from _base_parser import BaseParser, CommonSettings


class CrcSus(BaseParser, CommonSettings):
    """Command line application for printing an account's service unit allocation"""

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcSus, self).__init__()

        default_group = self.run_command("id -gn")
        self.add_argument('account', default=default_group, nargs='?', help='slurm account name')

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

        allocations = {cluster: db_record[cluster] for cluster in self.cluster_names}
        return allocations

    def build_output_string(self, account, **allocation):
        """Build a string describing an account's service unit allocation

        Args:
            account: The name of the account
            allocation: The number of service units allocated for each cluster

        Returns:
            A string summarizing the account allocation
        """

        output_lines = ['Account {}'.format(account)]
        cluster_name_length = max(len(cluster) for cluster in self.cluster_names)

        for cluster in self.cluster_names:
            cluster_name = cluster.rjust(cluster_name_length)
            output_lines.append(' cluster {} has {} SUs'.format(cluster_name, allocation.get(cluster, 0)))

        return '\n'.join(output_lines)

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
