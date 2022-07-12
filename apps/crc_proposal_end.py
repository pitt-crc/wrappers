"""Print the end date for an account's proposal

Command Line Interface
----------------------

.. argparse::
   :nodescription:
   :module: apps.crc_proposal_end
   :func: CrcProposalEnd
   :prog: crc-proposal-end
"""

import dataset

from ._base_parser import BaseParser
from ._system_info import Shell


class CrcProposalEnd(BaseParser):
    """Display the end date for an account's current CRC proposal."""

    banking_db_path = 'sqlite:////ihome/crc/bank/crc_bank.db'

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcProposalEnd, self).__init__()

        default_group = Shell.run_command("id -gn")
        self.add_argument(
            'account', default=default_group, nargs='?',
            help=f'the name of the Slurm account [default: {default_group}]')

    def get_proposal_end_date(self, account):
        """Get the proposal end date for a given account

        Args:
            account: The name of the account
        """

        database = dataset.connect(self.banking_db_path)
        table = database['proposal']

        db_record = table.find_one(account=account)
        if db_record is None:
            self.error("The account: {0} doesn't appear to exist".format(account))

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
