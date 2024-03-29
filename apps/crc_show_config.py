"""Display the slurm configuration for a given cluster/partition."""

from argparse import Namespace
from typing import Dict

from .utils.cli import BaseParser
from .utils.system_info import Shell, Slurm


class CrcShowConfig(BaseParser):
    """Display information about the current Slurm configuration."""

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcShowConfig, self).__init__()

        self.add_argument('-c', '--cluster', required=True, help='print partitions for the given cluster')
        self.add_argument('-p', '--partition', help='print information about nodes in the given partition')
        self.add_argument('-z', '--print-command', action='store_true',
                          help='print the equivalent slurm command and exit')

    @staticmethod
    def get_partition_info(cluster: str, partition: str) -> Dict[str, str]:
        """Return a dictionary of Slurm settings as configured on a given partition

        Args:
            cluster: The name of the cluster to get settings for
            partition: The name of the partition in the given cluster

        Returns:
            A dictionary of job information fetched from ``scontrol``
        """

        scontrol_command = f"scontrol -M {cluster} show partition {partition}"
        cmd_out = Shell.run_command(scontrol_command).split()

        partition_info = {}
        for slurm_option in cmd_out:
            split_values = slurm_option.split('=')
            partition_info[split_values[0]] = split_values[1]

        return partition_info

    def print_node(self, cluster: str, partition: str) -> None:
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
        nodes_info = Shell.run_command(f"scontrol show hostname {partition_nodes}")
        node = nodes_info.split()[0]
        print(Shell.run_command(f"scontrol -M {cluster} show node {node}"))

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        If a partition is specified (with or without a cluster name), print a
        summary for that partition.

        If only the cluster is specified, print a summary for all available
        partitions.

        Args:
            args: Parsed command line arguments
        """

        if args.partition:
            if args.partition not in Slurm.get_partition_names(args.cluster):
                self.error(f'Partition {args.partition} is not part of cluster {args.cluster}')

            self.print_node(args.cluster, args.partition)

        else:
            # Summarize all available partitions
            print(Shell.run_command(f"scontrol -M {args.cluster} show partition"))
