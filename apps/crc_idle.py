"""Command line application for listing idle Slurm resources.

The `crc-idle` application queries each cluster partition and summarizes
how many CPU cores or GPUs are currently available. Drained or downed nodes
are reported as having zero available resources.
"""

import re
from argparse import Namespace
from collections import defaultdict

from .utils import Shell, Slurm
from .utils.cli import BaseParser


class CrcIdle(BaseParser):
    """Display idle Slurm resources across cluster partitions."""

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

    def get_cluster_list(self, args: Namespace) -> tuple[str, ...]:
        """Return which clusters to report on based on command line arguments.

        Defaults to all known clusters if none are explicitly specified.

        Args:
            args: Parsed command line arguments.

        Returns:
            A tuple of cluster names as strings.
        """

        all_clusters = tuple(self.cluster_types.keys())
        specified = tuple(c for c in all_clusters if getattr(args, c))
        return specified or all_clusters

    @staticmethod
    def _count_idle_cpu_resources(cluster: str, partition: str) -> dict[int, dict[str, int]]:
        """Return idle CPU core counts and free memory statistics per node group.

        Nodes in a downed or drained state are reported as having zero idle cores
        and zero free memory.

        Args:
            cluster: The name of the cluster to query.
            partition: The name of the partition within the cluster.

        Returns:
            A dictionary mapping idle core count to a record containing the number
            of nodes at that count along with minimum and maximum free memory in MB.
        """

        # Use `sinfo` command to determine the status of each node in the given partition
        command = f'sinfo -h -M {cluster} -p {partition} -N -o %N,%C,%e,%t'
        slurm_data = Shell.run_command(command).strip().split()

        # Count the number of nodes having a given number of idle cores/GPUs
        result: dict[int, dict[str, int]] = {}
        for node_info in slurm_data:
            _, resource_data, free_mem, node_state = node_info.split(',')

            # If the node is in a downed state, report 0 resource availability.
            if any(key in node_state for key in ('down', 'drain')):
                idle, free_mem = 0, 0

            else:
                _, idle, _, _ = (int(x) for x in resource_data.split('/'))

            # Handle cases where sinfo reports 'N/A' for free memory
            try:
                free_mem = int(free_mem)

            except (ValueError, TypeError):
                free_mem = 0

            if idle not in result:
                result[idle] = {'count': 1, 'min_free_mem': free_mem, 'max_free_mem': free_mem}

            else:
                result[idle]['count'] += 1
                result[idle]['min_free_mem'] = min(result[idle]['min_free_mem'], free_mem)
                result[idle]['max_free_mem'] = max(result[idle]['max_free_mem'], free_mem)

        return result

    @staticmethod
    def _count_idle_gpu_resources(cluster: str, partition: str) -> dict[int, dict[str, int]]:
        """Return idle GPU counts and free memory statistics per node group.

        Nodes in a drained state are reported as having zero idle GPUs and zero
        free memory.

        Args:
            cluster: The name of the cluster to query.
            partition: The name of the partition within the cluster.

        Returns:
            A dictionary mapping idle GPU count to a record containing the number
            of nodes at that count along with minimum and maximum free memory in MB.
        """

        # Use `sinfo` command to determine the status of each node in the given partition
        fmt = "NodeList:'_',gres:5'_',gresUsed:12'_',StateCompact:'_',FreeMem ' '"
        command = f"sinfo -h -M {cluster} -p {partition} -N --Format={fmt}"
        slurm_data = Shell.run_command(command).strip().split()

        # Count the number of nodes having a given number of idle cores/GPUs
        result: dict[int, dict[str, int]] = {}
        for node_info in slurm_data:
            _, total, allocated, state, free_mem = node_info.split('_')

            if re.search('drain', state):
                idle, free_mem = 0, 0

            else:
                total_match = re.search(r'(\d+)', total)
                allocated_match = re.search(r'(\d+)', allocated)
                total_gpus = int(total_match.group(1)) if total_match else 0
                allocated_gpus = int(allocated_match.group(1)) if allocated_match else 0

                # Ensure idle value is never negative
                idle = max(0, total_gpus - allocated_gpus)

            # Handle cases where sinfo reports 'N/A' for free memory
            try:
                free_mem = int(free_mem)

            except (ValueError, TypeError):
                free_mem = 0

            if idle not in result:
                result[idle] = {'count': 1, 'min_free_mem': free_mem, 'max_free_mem': free_mem}

            else:
                result[idle]['count'] += 1
                result[idle]['min_free_mem'] = min(result[idle]['min_free_mem'], free_mem)
                result[idle]['max_free_mem'] = max(result[idle]['max_free_mem'], free_mem)

        return result

    def count_idle_resources(self, cluster: str, partition: str) -> dict[int, dict[str, int]]:
        """Return idle resource counts for a given cluster partition.

        Dispatches to the appropriate method based on the cluster type (CPU or GPU).

        Args:
            cluster: The name of the cluster to query.
            partition: The name of the partition within the cluster.

        Returns:
            A dictionary mapping idle resource count to node statistics.

        Raises:
            ValueError: If the cluster type is not recognized.
        """

        cluster_type = self.cluster_types[cluster]
        if cluster_type == 'GPUs':
            return self._count_idle_gpu_resources(cluster, partition)

        if cluster_type == 'cores':
            return self._count_idle_cpu_resources(cluster, partition)

        raise ValueError(f'Unknown cluster type: {cluster_type}')

    def print_partition_summary(self, cluster: str, partition: str, idle_resources: dict) -> None:
        """Print a summary of idle resources for a single partition.

        Args:
            cluster: The name of the cluster.
            partition: The name of the partition within the cluster.
            idle_resources: A dictionary mapping idle resource count to node statistics.
        """

        output_width = 70
        header = f'Cluster: {cluster}, Partition: {partition}'
        unit = self.cluster_types[cluster]

        print(header)
        print('=' * output_width)

        for idle, nodes in sorted(idle_resources.items()):
            min_mem = nodes['min_free_mem'] / 1024
            max_mem = nodes['max_free_mem'] / 1024
            print(f'{nodes["count"]:4d} nodes w/ {idle:3d} idle {unit} {min_mem:,.2f}G - {max_mem:,.2f}G min-max free memory')

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
