#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""Print the end date for an account's proposal"""

import dataset

from _base_parser import BaseParser


class CrcProposalEnd(BaseParser):
    """Command line application for printing an account's proposal end date"""

    db_path = 'sqlite:////ihome/crc/bank/crc_bank.db'

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcProposalEnd, self).__init__()
        self.add_argument('account', help='the Slurm account')

    def get_proposal_end_date(self, account):
        """Get the proposal end date for a given account

        Args:
            account: The name of the account
        """

        db = dataset.connect(self.db_path)
        table = db['proposal']

        db_record = table.find_one(account=account)
        if db_record is None:
            self.error("ERROR: The account: {0} doesn't appear to exist".format(account))

        return db_record['end_date']

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        end_date = self.get_proposal_end_date(args.account)

        # Format the account name and end date as an easy-to-read string
        string_template = "Proposal ends on {1} for account {0} on H2P"
        output_string = string_template.format(args.account, end_date.strftime("%m/%d/%y"))
        print(output_string)


if __name__ == '__main__':
    CrcProposalEnd().execute()
