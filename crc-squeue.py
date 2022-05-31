#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""crc-sqeueue.py -- An squeue Slurm helper
Usage:
    crc-squeue.py [-hvasw]

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-squeue.py
    -a --all                        Show all jobs
    -s --start                      Add the approximate start time
    -w --watch                      Updates information every 10 seconds
"""

from os import path
from os import system, environ

from docopt import docopt

from _version import __version__

__app_name__ = path.basename(__file__)

try:
    # Useful variables to reduce duplication
    user = "-u {0}".format(environ['USER'])
    squeue = "squeue -M all"
    watch = "-i 10"
    output_user_format = "-o '%.7i %.3P %.35j %.2t %.12M %.6D %.4C %.20R'"
    output_all_format = "-o '%.7i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.20R'"
    output_user_format_start = "-o '%.7i %.3P %.35j %.2t %.12M %.6D %.4C %.20R %.20S'"
    output_all_format_start = "-o '%.7i %.3P %.6a %.6u %.35j %.2t %.12M %.6D %.4C %.20R %.20S'"

    arguments = docopt(__doc__, version='{} version {}'.format(__app_name__, __version__))

    if arguments['--all'] and arguments['--start'] and arguments['--watch']:
        system("{0} {1} {2}".format(squeue, watch, output_all_format_start))
    elif arguments['--all'] and arguments['--start']:
        system("{0} {1}".format(squeue, output_all_format_start))
    elif arguments['--all'] and arguments['--watch']:
        system("{0} {1} {2}".format(squeue, watch, output_all_format))
    elif arguments['--start'] and arguments['--watch']:
        system("{0} {1} {2} {3}".format(squeue, user, watch, output_user_format_start))
    elif arguments['--all']:
        system("{0} {1}".format(squeue, output_all_format))
    elif arguments['--start']:
        system("{0} {1} {2}".format(squeue, user, output_user_format_start))
    elif arguments['--watch']:
        system("{0} {1} {2} {3}".format(squeue, user, watch, output_user_format))
    else:
        system("{0} {1} {2}".format(squeue, user, output_user_format))

except KeyboardInterrupt:
    exit('Interrupt detected! exiting...')
