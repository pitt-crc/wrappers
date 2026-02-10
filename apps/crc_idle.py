"""Command line application for listing idle Slurm resources.

The application relies on the info command to identify idle resources and
summarize how many resources are available on each cluster partition.
Resource summaries are provided for GPU and CPU partitions.
"""

import re
from argparse import Namespace
from collections import defaultdict

from .utils import Shell, Slurm
from .utils.cli import BaseParser


class CrcIdle(BaseParser):
    """Display idle Slurm resources."""

    # Specify the type of resource available on each cluster
    # Either `cores` or `GPUs` depending on the cluster type
    cluster_types = defaultdict(
        lambda: 'cores',
        smp='cores',
        gpu='GPUs',
        mpi='cores',
        htc='cores',
        teach='cores',
    )

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super(CrcIdle, self).__init__()
        self.add_argument('-s', '--smp', action='store_true', help='list idle resources on the smp cluster')
        self.add_argument('-g', '--gpu', action='store_true', help='list idle resources on the gpu cluster')
        self.add_argument('-m', '--mpi', action='store_true', help='list idle resources on the mpi cluster')
        self.add_argument('-d', '--htc', action='store_true', help='list idle resources on the htc cluster')
        self.add_argument('-t', '--teach', action='store_true', help='list idle resources on the teach cluster')
        self.add_argument('-p', '--partition', nargs='+', help='only include information for specific partitions')

    def get_cluster_list(self, args: Namespace) -> tuple[str]:
        """Return a list of clusters specified by command line arguments.

        Returns a tuple of clusters specified by command line arguments. If no
        clusters were specified, then return a tuple of all cluster names.

        Args:
            args: Parsed command line arguments

        Returns:
            A tuple of cluster names
        """

        # Select only the specified clusters
        argument_clusters = tuple(self.cluster_types.keys())
        specified_clusters = tuple(filter(lambda cluster: getattr(args, cluster), argument_clusters))

        # Default to returning all clusters
        return specified_clusters or argument_clusters

    @staticmethod
    def _count_idle_cpu_resources(cluster: str, partition: str) -> dict[int, dict[str, int]]:
        """Return the idle CPU resources on a given cluster partition.

        Args:
            cluster: The cluster to print a summary for.
            partition: The partition in the parent cluster.

        Returns:
            A dictionary mapping the number of idle resources to a dictionary with the number of nodes with that many
            idle resources, minimum free memory, and maximum free memory on these nodes.
        """

        # Use `sinfo` command to determine the status of each node in the given partition
        command = f'sinfo -h -M {cluster} -p {partition} -N -o %N,%C,%e,%t'
        slurm_data = Shell.run_command(command).strip().split()

        # Count the number of nodes having a given number of idle cores/GPUs
        return_dict = dict()
        for node_info in slurm_data:
            _, resource_data, free_mem, node_state = node_info.split(',')

            # If the node is in a downed state, report 0 resource availability.
            down_keys = ['down', 'drain']
            if any(key in node_state for key in down_keys):
                idle = 0
                free_mem = 0
            else:
                allocated, idle, other, total = [int(x) for x in resource_data.split('/')]

            # Handle cases where sinfo reports 'N/A' for free memory
            try:
                free_mem = int(free_mem)
            except (ValueError, TypeError):
                free_mem = 0

            if idle not in return_dict:
                return_dict[idle] = {
                    'count': 1,
                    'min_free_mem': free_mem,
                    'max_free_mem': free_mem
                }
            else:
                return_dict[idle]['count'] += 1
                return_dict[idle]['min_free_mem'] = min(return_dict[idle]['min_free_mem'], free_mem)
                return_dict[idle]['max_free_mem'] = max(return_dict[idle]['max_free_mem'], free_mem)

        return return_dict

    @staticmethod
    def _count_idle_gpu_resources(cluster: str, partition: str) -> dict[int, dict[str, int]]:
        """Return idle GPU resources on a given cluster partition.

        If the host node is in a `drain` state, the GPUs are reported as unavailable.

        Args:
            cluster: The cluster to print a summary for.
            partition: The partition in the parent cluster.

        Returns:
            A dictionary mapping the number of idle resources to the number of nodes with that many idle resources.
        """

        # Use `sinfo` command to determine the status of each node in the given partition
        slurm_output_format = "NodeList:'_',gres:5'_',gresUsed:12'_',StateCompact:'_',FreeMem ' '"
        command = f"sinfo -h -M {cluster} -p {partition} -N --Format={slurm_output_format}"
        slurm_data = Shell.run_command(command).strip().split()

        # Count the number of nodes having a given number of idle cores/GPUs
        return_dict = dict()
        for node_info in slurm_data:
            _, total, allocated, state, free_mem = node_info.split('_')

            if re.search("drain", state):
                idle = 0
                free_mem = 0
            else:
                allocated = int(allocated[-1:])
                total = int(total[-1:])
                idle = total - allocated

            # Handle cases where sinfo reports 'N/A' for free memory
            try:
                free_mem = int(free_mem)
            except (ValueError, TypeError):
                free_mem = 0

            if idle not in return_dict:
                return_dict[idle] = {
                    'count': 1,
                    'min_free_mem': free_mem,
                    'max_free_mem': free_mem
                }
            else:
                return_dict[idle]['count'] += 1
                return_dict[idle]['min_free_mem'] = min(return_dict[idle]['min_free_mem'], free_mem)
                return_dict[idle]['max_free_mem'] = max(return_dict[idle]['max_free_mem'], free_mem)

        return return_dict

    def count_idle_resources(self, cluster: str, partition: str) -> dict[int, dict[str, int]]:
        """Determine the number of idle resources on a given cluster partition.

        The returned dictionary maps the number of idle resources (e.g., cores)
        to the number of nodes in the partition having that many resources idle.

        Args:
            cluster: The cluster to print a summary for.
            partition: The partition in the parent cluster.

        Returns:
            A dictionary mapping idle resources to number of nodes.
        """

        cluster_type = self.cluster_types[cluster]
        if cluster_type == 'GPUs':
            return self._count_idle_gpu_resources(cluster, partition)

        elif cluster_type == 'cores':
            return self._count_idle_cpu_resources(cluster, partition)

        raise ValueError(f'Unknown cluster type: {cluster}')

    def print_partition_summary(self, cluster: str, partition: str, idle_resources: dict) -> None:
        """Print a summary of idle resources in a single partition

        Args:
            cluster: The cluster to print a summary for
            partition: The partition in the parent cluster
            idle_resources: Dictionary mapping idle resources to number of nodes
        """

        output_width = 70
        header = f'Cluster: {cluster}, Partition: {partition}'
        unit = self.cluster_types[cluster]

        print(header)
        print('=' * output_width)
        for idle, nodes in sorted(idle_resources.items()):
            print(f'{nodes["count"]:4d} nodes w/ {idle:3d} idle {unit} {(nodes["min_free_mem"]/1024):,.2f}G - '
                  f'{(nodes["max_free_mem"]/1024):,.2f}G min-max free memory')

        if not idle_resources:
            print(' No idle resources')

        print('')

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application.

        Args:
            args: Parsed command line arguments.
        """

        for cluster in self.get_cluster_list(args):
            partitions_to_print = args.partition or Slurm.get_partition_names(cluster)
            for partition in partitions_to_print:
                idle_resources = self.count_idle_resources(cluster, partition)
                self.print_partition_summary(cluster, partition, idle_resources)
