#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""A simple wrapper around the Slurm ``scontrol`` command"""

from _base_parser import BaseParser, CommonSettings


class CrcScontrol(BaseParser, CommonSettings):
    """Command line application for fetching data from the Slurm ``scontrol`` utility"""

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcScontrol, self).__init__()

        valid_clusters = tuple(self.cluster_partitions)
        self.add_argument('-c', '--cluster', choices=valid_clusters, help='print partitions for the given cluster')
        self.add_argument('-p', '--partition', help='print information about nodes in the given partition')

    def print_node(self, cluster, partition):
        """Print the slurm configuration of a given cluster and partition

        Args:
            cluster: The name of the cluster
            partition: The name of the partition on the cluster
        """

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

        if args.cluster and args.partition:
            self.print_help()
            self.exit(0)

        # If the cluster is specified, summarize the available partitions
        if args.cluster:
            print(self.run_command("scontrol -M {} show partition".format(args.cluster)))
            self.exit(0)

        # If the partition is specified, find the corresponding cluster
        for cluster, partitions in self.cluster_partitions.items():
            if args.partition in partitions:
                self.print_node(cluster, args.partition)
                self.exit(0)

        self.error("Error: I don't recognize partition: {}".format(args.partition))


if __name__ == '__main__':
    CrcScontrol().execute()
