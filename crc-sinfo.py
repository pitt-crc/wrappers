#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""crc-sinfo.py -- An sinfo Slurm helper
Usage:
    crc-sinfo.py [-hv]

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-sinfo.py
"""

from os import system

from docopt import docopt

try:

    arguments = docopt(__doc__, version='crc-sinfo.py version 0.0.1')

    system("sinfo -M all")

except KeyboardInterrupt:
    exit('Interrupt detected! exiting...')
