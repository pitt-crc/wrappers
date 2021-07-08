#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
''' crc-scancel.py -- An scancel Slurm helper
Usage:
    crc-scancel.py (-h | --help)
    crc-scancel.py (-v | --version)
    crc-scancel.py <job_id>

Positional Arguments:
    <job_id>                        The job's ID

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-scancel.py
'''

try:
    # Some imports functions and libraries
    from docopt import docopt
    from os import environ
    from subprocess import Popen, PIPE
    from readchar import readchar
    from sys import stdout

    # Magical mystical docopt
    arguments = docopt(__doc__, version='crc-scancel.py version 0.0.1')

    # Job exists on any of the clusters?
    output = {}
    for cluster in ['smp', 'gpu', 'mpi', 'htc', 'invest']:
        #output.append(popen("squeue {0} -j {1} -M {2}".format(user, arguments['<job_id>'], i)).read())
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
