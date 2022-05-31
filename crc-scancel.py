#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""crc-scancel.py -- An scancel Slurm helper
Usage:
    crc-scancel.py (-h | --help)
    crc-scancel.py (-v | --version)
    crc-scancel.py <job_id>

Positional Arguments:
    <job_id>                        The job's ID

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-scancel.py
"""

from os import environ
from os import path
from subprocess import Popen, PIPE
from sys import stdout

from docopt import docopt
from readchar import readchar

from _version import __version__

__app_name__ = path.basename(__file__)

try:
    # Magical mystical docopt
    arguments = docopt(__doc__, version='{} version {}'.format(__app_name__, __version__))

    # Job exists on any of the clusters?
    output = {}
    for cluster in ['smp', 'gpu', 'mpi', 'htc', 'invest']:
        # output.append(popen("squeue {0} -j {1} -M {2}".format(user, arguments['<job_id>'], i)).read())
        sp = Popen(['squeue', '-h', '-u', environ['USER'], '-j', arguments['<job_id>'], '-M', cluster], stdout=PIPE, stderr=PIPE)
        out, err = sp.communicate()
        output[cluster] = out

    # Check that the stdout contains the job_id, ask the user if we can delete it
    for clus, entry in output.items():
        if arguments['<job_id>'] in entry:
            spl = entry.splitlines()
            stdout.write("Would you like to cancel job {0} on cluster {1}? (y/N): ".format(arguments['<job_id>'], clus))
            choice = readchar()
            if choice.lower() == 'y':
                Popen(['scancel', '-M', clus, arguments['<job_id>']])
            print('')

except KeyboardInterrupt:
    exit('Interrupt detected! exiting...')
