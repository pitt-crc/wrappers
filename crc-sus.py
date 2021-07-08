#!/usr/bin/env python
''' crc-sus.py -- Get SUs from crc-bank.db
Usage:
    crc-sus.py <account> 
    crc-sus.py -h | --help
    crc-sus.py -v | --version

Positional Arguments:
    <account>       The Slurm account

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-sus.py
'''


# Test:
# 1. Make sure item exists
def check_item_in_table(table, account):
    if table.find_one(account=account) is None:
        exit("ERROR: This account has no SUs?")


import dataset
from docopt import docopt

# clusters
clusters = ["smp", "gpu", "mpi", "htc"]

# The magical mystical docopt line
arguments = docopt(__doc__, version='crc-sus.py version 0.0.1')

# Connect to the database and get the limits table
# Absolute path ////
db = dataset.connect('sqlite:////ihome/crc/bank/crc_bank.db')
table = db['proposal']

# Print out SUs
string = "Account {0} on {1}"
od = table.find_one(account=arguments['<account>'])
sus = ["cluster {cluster} has {od[cluster]} SUs" for cluster in clusters]
print(string.format(arguments['<account>'], ", ".join(sus)))
