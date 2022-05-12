#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""crc-sinfo.py -- An sinfo Slurm helper
Usage:
    crc-sinfo.py [-hv]

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-sinfo.py
"""

try:
    # Some imports functions and libraries
    from docopt import docopt
    from os import system

    arguments = docopt(__doc__, version='crc-sinfo.py version 0.0.1')

    system("sinfo -M all")

except KeyboardInterrupt:
    exit('Interrupt detected! exiting...')
