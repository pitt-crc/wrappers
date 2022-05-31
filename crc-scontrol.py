#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""crc-scontrol.py -- An scontrol Slurm helper
Usage:
    crc-scontrol.py (-c <cluster> | -p <partition>) [-hv]

Positional Arguments:
    -c --cluster <cluster>          Print partitions for <cluster>
    -p --partition <partition>      Prints information about node in <partition>

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-scontrol.py
"""

from os import path
from random import choice
from shlex import split
from subprocess import Popen, PIPE

from docopt import docopt

from _version import __version__

__app_name__ = path.basename(__file__)


def print_command(command):
    sp = Popen(split(command), stdout=PIPE)
    print(sp.communicate()[0].strip())


def run_command_dict(command):
    sp = Popen(split(command), stdout=PIPE)
    out = sp.communicate()[0].strip().split()
    cluster_dict = {}
    for op in out:
        sp = op.split('=')
        cluster_dict[sp[0]] = sp[1]
    return cluster_dict


def run_command(command):
    sp = Popen(split(command), stdout=PIPE)
    return sp.communicate()[0].strip().split()


def print_node(cluster):
    cluster_dict = run_command_dict("scontrol -M {} show partition {}".format(cluster, arguments['--partition']))
    node = choice(run_command("scontrol show hostname {}".format(cluster_dict['Nodes'])))
    print_command("scontrol -M {} show node {}".format(cluster, node))


try:
    arguments = docopt(__doc__, version='{} version {}'.format(__app_name__, __version__))

    smp_partitions = ['smp', 'high-mem', "legacy"]
    gpu_partitions = ['gtx1080', 'titanx', 'titan', 'k40']
    mpi_partitions = ['opa', 'ib', "opa-high-mem"]
    htc_partitions = ['htc']

    if arguments['--cluster']:
        if arguments['--cluster'] in ['smp', 'gpu', 'mpi', 'htc']:
            print_command("scontrol -M {} show partition".format(arguments['--cluster']))
        else:
            print("Error: I don't recognize cluster: {}".format(arguments['--cluster']))
    elif arguments['--partition']:
        if arguments['--partition'] in smp_partitions:
            print_node("smp")
        elif arguments['--partition'] in gpu_partitions:
            print_node("gpu")
        elif arguments['--partition'] in mpi_partitions:
            print_node("mpi")
        elif arguments['--partition'] in htc_partitions:
            print_node("htc")
        else:
            print("Error: I don't recognize partition: {}".format(arguments['--partition']))

except KeyboardInterrupt:
    exit('Interrupt detected! exiting...')
