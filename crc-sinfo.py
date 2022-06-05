#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""crc-sinfo.py -- An sinfo Slurm helper
Usage:
    crc-sinfo.py [-hv]

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-sinfo.py
"""

from os import path
from os import system

from docopt import docopt

from _base_parser import BaseParser

__version__ = BaseParser.get_semantic_version()
__app_name__ = path.basename(__file__)

try:

    arguments = docopt(__doc__, version='{} version {}'.format(__app_name__, __version__))

    system("sinfo -M all")

except KeyboardInterrupt:
    exit('Interrupt detected! exiting...')
