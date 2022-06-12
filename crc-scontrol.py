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

    def get_partition_info(self, cluster, partition):
        """Return a dictionary of Slurm settings as configured on a given partition

        Args:
            cluster: The name of the cluster to get settings for
            partition: The name of the partition in the given cluster
        """

        scontrol_command = "scontrol -M {} show partition {}".format(cluster, partition)
        cmd_out = self.run_command(scontrol_command).split()

        partition_info = {}
        for slurm_option in cmd_out:
            option_name, option_value = slurm_option.split('=')
            partition_info[option_name] = option_value

        return partition_info

    def print_node(self, cluster, partition):
        """Print the slurm configuration of a given cluster and partition

        Args:
            cluster: The name of the cluster
            partition: The name of the partition on the cluster
        """

        # Retrieve a list of nodes available in a given partition
        partition_info = self.get_partition_info(cluster, partition)
        partition_nodes = partition_info['Nodes']

        # Get slurm settings for each node in the partition
        # Only print out values for a single node
        # Assume the first node is representative of the partition
        nodes_info = self.run_command("scontrol show hostname {}".format(partition_nodes))
        node = nodes_info.split()[0]
        print(self.run_command("scontrol -M {} show node {}".format(cluster, node)))

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        if args.cluster and args.partition:
            self.print_help()

        # If the cluster is specified, summarize the available partitions
        elif args.cluster:
            print(self.run_command("scontrol -M {} show partition".format(args.cluster)))

        # If the partition is specified, find the corresponding cluster
        else:
            for cluster, partitions in self.cluster_partitions.items():
                if args.partition in partitions:
                    self.print_node(cluster, args.partition)

        self.error("Error: I don't recognize partition: {}".format(args.partition))


if __name__ == '__main__':
    CrcScontrol().execute()
