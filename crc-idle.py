#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""Command line application for listing idle Slurm resources"""

from _base_parser import BaseParser
from _utils import Shell, SlurmInfo


class CrcIdle(BaseParser):
    """Command line application for listing idle Slurm resources"""

    # The type of resource available on a cluster
    # Either ``cores`` or ``GPUs`` depending on the cluster type
    cluster_types = {
        'smp': 'cores',
        'gpu': 'GPUs',
        'mpi': 'cores',
        'htc': 'cores'
    }
    default_type = 'cores'

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcIdle, self).__init__()
        self.add_argument('-s', '--smp', action='store_true', help='show idle resources on the smp cluster')
        self.add_argument('-g', '--gpu', action='store_true', help='show idle resources on the gpu cluster')
        self.add_argument('-m', '--mpi', action='store_true', help='show idle resources on the mpi cluster')
        self.add_argument('-i', '--invest', action='store_true', help='show idle resources on the invest cluster')
        self.add_argument('-d', '--htc', action='store_true', help='show idle resources on the htc cluster')
        self.add_argument('-p', '--partition', nargs='+', help='Specify non-default partition')

    @staticmethod
    def get_cluster_list(args):
        """Return a list of clusters specified in the command line arguments

        Returns a tuple of clusters specified by command line arguments. If no
        clusters were specified, then return a tuple of all cluster names.

        Args:
            args: Parsed command line arguments

        Returns:
            A tuple fo cluster names
        """

        argument_options = ('smp', 'gpu', 'mpi', 'invest', 'htc')
        argument_clusters = tuple(filter(lambda cluster: getattr(args, cluster), argument_options))

        # Default to returning all clusters
        return argument_clusters or argument_options

    @staticmethod
    def _idle_cpu_resources(cluster, partition):
        """Return the idle CPU resources on a given cluster partition

        Args:
            cluster: The cluster to print a summary for
            partition: The partition in the parent cluster

        Returns:
            A dictionary mapping idle resources to number of nodes
        """

        # Use `sinfo` command to determine the status of each node in the given partition
        command = 'sinfo -h -M {0} -p {1} -N -o %N,%C'.format(cluster, partition)
        stdout = Shell.run_command(command)
        slurm_data = stdout.strip().split()

        # Count the number of nodes having a given number of idle cores/GPUs
        return_dict = dict()
        for node_info in slurm_data:
            node_name, resource_data = node_info.split(',')
            # Return values include: allocated, idle, other, total
            _, idle, _, _ = [int(x) for x in resource_data.split('/')]
            return_dict[idle] = return_dict.setdefault(idle, 0) + 1

        return return_dict

    @staticmethod
    def _idle_gpu_resources(cluster, partition):
        """Return the idle GPU resources on a given cluster partition

           If the host node is in 'drain' state, the GPUs are reported as unavailable.

        Args:
            cluster: The cluster to print a summary for
            partition: The partition in the parent cluster

        Returns:
            A dictionary mapping idle resources to number of nodes
        """

        # Use `sinfo` command to determine the status of each node in the given partition
        command = "sinfo -h -M {0} -p {1} -N --Format=NodeList:'_',gres:5'_',gresUsed:12'_',StateCompact:' '".format(cluster, partition)
        stdout = Shell.run_command(command)
        slurm_data = stdout.strip().split()

        # Count the number of nodes having a given number of idle cores/GPUs
        return_dict = dict()
        for node_info in slurm_data:
            # node_name, total, allocated, node state
            _, total, allocated, state = node_info.split('_')

            # If the node is in a downed state, report 0 resource availability.
            if state in ['drain']:
                idle = 0

            else:
                allocated = int(allocated[-1:])
                total = int(total[-1:])
                idle = total - allocated

            return_dict[idle] = return_dict.setdefault(idle, 0) + 1

        return return_dict

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

        if self.cluster_types.get(cluster, self.default_type) == 'GPUs':
            return self._idle_gpu_resources(cluster, partition)

        else:
            return self._idle_cpu_resources(cluster, partition)

    def print_partition_summary(self, cluster, partition):
        """Print a summary of idle resources in a single partition

        Args:
            cluster: The cluster to print a summary for
            partition: The partition in the parent cluster
        """

        resource_allocation = self.count_idle_resources(cluster, partition)

        output_width = 30
        header = 'Cluster: {0}, Partition: {1}'.format(cluster, partition)
        unit = self.cluster_types.get(cluster, self.default_type)

        print(header)
        print('=' * output_width)
        for idle, nodes in sorted(resource_allocation.items()):
            print('{0:4d} nodes w/ {1:3d} idle {2}'.format(nodes, idle, unit))

        if not resource_allocation:
            print(' No idle resources')

        print('')

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        for cluster in self.get_cluster_list(args):
            partitions_to_print = args.partition or SlurmInfo.get_partition_names(cluster)
            for partition in partitions_to_print:
                self.print_partition_summary(cluster, partition)


if __name__ == '__main__':
    CrcIdle().execute()
