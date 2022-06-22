#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""Command line application for listing idle Slurm resources"""

from _base_parser import BaseParser, CommonSettings


class CrcIdle(BaseParser, CommonSettings):
    """Command line application for listing idle Slurm resources"""

    # The type of resource available on a cluster
    # Either ``cores`` or ``GPUs`` depending on the cluster type
    cluster_types = {
        'smp': 'cores',
        'gpu': 'GPUs',
        'mpi': 'cores',
        'htc': 'cores'
    }

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcIdle, self).__init__()
        self.add_argument('-s', '--smp', action='store_true', help='show idle resources on the smp cluster')
        self.add_argument('-g', '--gpu', action='store_true', help='show idle resources on the gpu cluster')
        self.add_argument('-m', '--mpi', action='store_true', help='show idle resources on the mpi cluster')
        self.add_argument('-i', '--invest', action='store_true', help='show idle resources on the invest cluster')
        self.add_argument('-d', '--htc', action='store_true', help='show idle resources on the htc cluster')
        self.add_argument('-p', '--partition', nargs='+', help='Specify non-default partition')

    def get_cluster_list(self, args):
        """Return a list of clusters specified in the command line arguments

        Returns a tuple of clusters specified by command line arguments. If no
        clusters were specified, then return a tuple of all cluster names.

        Args:
            args: Parsed command line arguments

        Returns:
            A tuple fo cluster names
        """

        all_clusters = tuple(self.cluster_partitions)
        argument_clusters = tuple(filter(lambda cluster: getattr(args, cluster), self.cluster_partitions))

        # Default to returning all clusters
        return argument_clusters or all_clusters

    def count_idle_resources(self, cluster, partition):
        """Determine the number of idle resources on a given cluster partition

        The returned dictionary maps the number of idle resources (e.g., cores)
        to the number of nodes in the partition having that many resources idle.

        Args:
            cluster: The cluster to print a summary for
            partition: The partition in the parent cluster

        Returns:
            A dictionary mapping idle resources to number of nodes
        """

        # Use `sinfo` command to determine the status of each node in the given partition
        command = 'sinfo -M {0} -p {1} -N -o %N,%C'.format(cluster, partition)
        stdout = self.run_command(command)

        first_line_of_data = 3
        slurm_data = stdout.strip().split()[first_line_of_data:]

        # Count the number of nodes having a given number of idle cores
        return_dict = {}
        for node_info in slurm_data:
            node_name, resource_data = node_info.split(',')
            allocated, idle, other, total = [int(x) for x in resource_data.split('/')]

            if idle > 0:
                return_dict.setdefault(idle, 0)
                return_dict[idle] += 1

        return return_dict

    def print_partition_summary(self, cluster, partition):
        """Print a summary of idle resources in a single partition

        Args:
            cluster: The cluster to print a summary for
            partition: The partition in the parent cluster
        """

        resource_allocation = self.count_idle_resources(cluster, partition)

        output_width = 30
        header = 'Cluster: {0}, Partition: {1}'.format(cluster, partition)
        unit = self.cluster_types[cluster]

        print(header.center(output_width))
        print('=' * output_width)
        for idle, nodes in sorted(resource_allocation.items()):
            print('{0:3d} nodes w/ {1:3d} idle {2}'.format(nodes, idle, unit))

        if not resource_allocation:
            print(' No idle resources')

        print('')

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        for cluster in self.get_cluster_list(args):
            partitions_to_print = args.partition or self.cluster_partitions[cluster]
            for partition in partitions_to_print:
                self.print_partition_summary(cluster, partition)


if __name__ == '__main__':
    CrcIdle().execute()
