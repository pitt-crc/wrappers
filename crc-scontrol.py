#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""A simple wrapper around the Slurm ``scontrol`` command"""

from random import choice
from shlex import split
from subprocess import Popen, PIPE

from _base_parser import BaseParser


def print_command(command):
    sp = Popen(split(command), stdout=PIPE)
    print(sp.communicate()[0].strip())


def run_command(command):
    sp = Popen(split(command), stdout=PIPE)
    return sp.communicate()[0].strip().split()


def run_command_dict(command):
    sp = Popen(split(command), stdout=PIPE)
    out = sp.communicate()[0].strip().split()
    cluster_dict = {}
    for op in out:
        sp = op.split('=')
        cluster_dict[sp[0]] = sp[1]
    return cluster_dict


class CrcScontrol(BaseParser):
    cluster_partitions = {
        'smp': ['smp', 'high-mem', "legacy"],
        'gpu': ['gtx1080', 'titanx', 'titan', 'k40'],
        'mpi': ['opa', 'ib', "opa-high-mem"],
        'htc': ['htc']
    }

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcScontrol, self).__init__()
        self.add_argument('-c', '--cluster', help='print partitions for the given cluster')
        self.add_argument('-p', '--partition', help='print information about nodes in the given partition')

    @staticmethod
    def print_node(cluster, partition):
        cluster_dict = run_command_dict("scontrol -M {} show partition {}".format(cluster, partition))
        node = choice(run_command("scontrol show hostname {}".format(cluster_dict['Nodes'])))
        print_command("scontrol -M {} show node {}".format(cluster, node))

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        if args.cluster:
            if args.cluster not in self.cluster_partitions:
                self.error("Error: I don't recognize cluster: {}".format(args.cluster))

            print_command("scontrol -M {} show partition".format(args.cluster))

        elif args.partition:
            if args.partition not in self.cluster_partitions[args.cluster]:
                self.error("Error: I don't recognize partition: {}".format(args.partition))

            self.print_node(args.cluster, args.partition)


if __name__ == '__main__':
    CrcScontrol().execute()
