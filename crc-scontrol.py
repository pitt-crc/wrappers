#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""A simple wrapper around the Slurm ``scontrol`` command"""

from shlex import split
from subprocess import Popen, PIPE

from _base_parser import BaseParser


class CrcScontrol(BaseParser):
    """Command line application for fetching data from the Slurm ``scontrol`` utility"""

    cluster_partitions = {
        'smp': ['smp', 'high-mem', "legacy"],
        'gpu': ['gtx1080', 'titanx', 'titan', 'k40'],
        'mpi': ['opa', 'ib', "opa-high-mem"],
        'htc': ['htc']
    }

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcScontrol, self).__init__()

        valid_clusters = tuple(self.cluster_partitions)
        self.add_argument('-c', '--cluster', choices=valid_clusters, help='print partitions for the given cluster')
        self.add_argument('-p', '--partition', help='print information about nodes in the given partition')

    @staticmethod
    def run_command(command):
        sp = Popen(split(command), stdout=PIPE)
        return sp.communicate()[0].strip()

    def print_node(self, cluster, partition):
        command = "scontrol -M {} show partition {}".format(cluster, partition)

        cluster_dict = {}
        for op in self.run_command(command).split():
            sp = op.split('=')
            cluster_dict[sp[0]] = sp[1]

        command_out = self.run_command("scontrol show hostname {}".format(cluster_dict['Nodes']))

        node = command_out.split()[0]
        print(self.run_command("scontrol -M {} show node {}".format(cluster, node)))

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        if args.cluster:
            print(self.run_command("scontrol -M {} show partition".format(args.cluster)))

        else:
            if args.partition not in self.cluster_partitions[args.cluster]:
                self.error("Error: I don't recognize partition: {}".format(args.partition))

            self.print_node(args.cluster, args.partition)


if __name__ == '__main__':
    CrcScontrol().execute()
