"""Command line application for displaying Slurm partition and node configuration.

The `crc-show-config` application wraps `scontrol` to display partition and
node-level Slurm settings for a given cluster. When a partition is specified,
configuration for a representative node in that partition is shown.
"""

from argparse import Namespace

from .utils.cli import BaseParser
from .utils.system_info import Shell, Slurm


class CrcShowConfig(BaseParser):
    """Display Slurm configuration for a given cluster or partition."""

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super(CrcShowConfig, self).__init__()
        self.add_argument('-c', '--cluster', required=True, help='print configuration details for the given cluster')
        self.add_argument('-p', '--partition', help='print configuration details for the given partition')
        self.add_argument('-z', '--print-command', action='store_true', help='print the equivalent Slurm command and exit')

    @staticmethod
    def get_partition_info(cluster: str, partition: str) -> dict[str, str]:
        """Return Slurm settings for a given partition as a dictionary.

        Args:
            cluster: The name of the cluster to query.
            partition: The name of the partition within the cluster.

        Returns:
            A dictionary of Slurm partition settings from `scontrol`.
        """

        output = Shell.run_command(f'scontrol -M {cluster} show partition {partition}').split()
        return {k: v for item in output for k, v in [item.split('=')]}

    def print_node(self, cluster: str, partition: str) -> None:
        """Print Slurm node configuration for a representative node in a partition.

        Args:
            cluster: The name of the cluster.
            partition: The name of the partition within the cluster.
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
        """Logic to evaluate when executing the application.

        Args:
            args: Parsed command line arguments.
        """

        if args.partition:
            if args.partition not in Slurm.get_partition_names(args.cluster):
                self.error(f'Partition {args.partition} is not part of cluster {args.cluster}.')

            self.print_node(args.cluster, args.partition)

        else:
            print(Shell.run_command(f'scontrol -M {args.cluster} show partition'))
