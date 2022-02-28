#!/usr/bin/env python
"""crc-sus.py -- Get SUs from crc-bank.db
Usage:
    crc-sus.py <account>
    crc-sus.py -h | --help
    crc-sus.py -v | --version

Positional Arguments:
    <account>       The Slurm account

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-sus.py
"""

import dataset
from docopt import docopt

arguments = docopt(__doc__, version='crc-sus.py version 0.0.1')

# Connect to the database and get the table with proposal service units
db = dataset.connect('sqlite:////ihome/crc/bank/crc_bank.db')
table = db['proposal']

# Ensure a proposal exists for the given account
db_record = table.find_one(account=arguments['<account>'])
if db_record is None:
    exit('ERROR: No proposal for the given account was found')

# Convert cluster SUs to strings
clusters = ('smp', 'gpu', 'mpi', 'htc')
sus_string = ['cluster {} has {} SUs'.format(cluster, db_record[cluster]) for cluster in clusters]

string_prefix = 'Account {}'.format(arguments['<account>'])
string_postfix = ', '.join(sus_string)
out_string = ' '.join((string_prefix, string_postfix))
print(out_string)
