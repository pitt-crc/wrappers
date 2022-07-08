"""Display the slurm configuration for a given cluster/partition"""

from .base_parser import BaseParser
from .system_info import Shell, SlurmInfo


class CrcShowConfig(BaseParser):
    """Command line application for fetching data from the Slurm ``scontrol`` utility"""

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcShowConfig, self).__init__()

        self.add_argument(
            '-c', '--cluster',
            required=True,
            choices=SlurmInfo.get_cluster_names(),
            help='print partitions for the given cluster')

        self.add_argument('-p', '--partition', help='print information about nodes in the given partition')

    @staticmethod
    def get_partition_info(cluster, partition):
        """Return a dictionary of Slurm settings as configured on a given partition

        Args:
            cluster: The name of the cluster to get settings for
            partition: The name of the partition in the given cluster
        """

        scontrol_command = "scontrol -M {} show partition {}".format(cluster, partition)
        cmd_out = Shell.run_command(scontrol_command).split()

        partition_info = {}
        for slurm_option in cmd_out:
            split_values = slurm_option.split('=')
            partition_info[split_values[0]] = split_values[1]

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
        nodes_info = Shell.run_command("scontrol show hostname {}".format(partition_nodes))
        node = nodes_info.split()[0]
        print(Shell.run_command("scontrol -M {} show node {}".format(cluster, node)))

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        If a partition is specified (with or without a cluster name), print a
        summary for that partition.

        If only the cluster is specified, print a summary for all available
        partitions.

        Args:
            args: Parsed command line arguments
        """

        if args.partition:
            if args.partition not in SlurmInfo.get_partition_names(args.cluster):
                self.error('Partition {} is not part of cluster {}'.format(args.partition, args.cluster))

            self.print_node(args.cluster, args.partition)

        else:
            # Summarize all available partitions
            print(Shell.run_command("scontrol -M {} show partition".format(args.cluster)))


if __name__ == '__main__':
    CrcShowConfig().execute()
