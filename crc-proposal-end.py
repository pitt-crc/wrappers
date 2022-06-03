#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""crc-proposal-end.py -- Get SUs from crc-bank.db
Usage:
    crc-proposal-end.py <account> 
    crc-proposal-end.py -h | --help
    crc-proposal-end.py -v | --version

Positional Arguments:
    <account>       The Slurm account

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-proposal-end.py
"""

from os import path

import dataset
from docopt import docopt

from _base_parser import BaseParser

__version__ = BaseParser.get_semantic_version()
__app_name__ = path.basename(__file__)


# Test:
# 1. Make sure item exists
def check_item_in_table(table, account):
    if table.find_one(account=account) is None:
        exit("ERROR: The account: {0} doesn't appear to exist".format(account))


# The magical mystical docopt line
arguments = docopt(__doc__, version='{} version {}'.format(__app_name__, __version__))

# Connect to the database and get the limits table
# Absolute path ////
db = dataset.connect('sqlite:////ihome/crc/bank/crc_bank.db')
table = db['proposal']

# Check that account exists
check_item_in_table(table, arguments['<account>'])

# Print out SUs
string = "Proposal ends on {1} for account {0} on H2P"
end_date = table.find_one(account=arguments['<account>'])['end_date']
print(string.format(arguments['<account>'], end_date.strftime("%m/%d/%y")))
