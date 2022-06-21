#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""Command line application for listing idle Slurm resources"""

from shlex import split
from subprocess import Popen, PIPE

from _base_parser import BaseParser, CommonSettings


class CrcIdle(BaseParser, CommonSettings):
    """Command line application for listing idle Slurm resources"""

    # The type of resource available on a cluster
    # Either ``cores`` or ``GPUs`` depending on the cluster type
    cluster_types = {
        "smp": 'cores',
        "gpu": 'GPUs',
        "mpi": 'cores',
        "htc": 'cores'
    }

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcIdle, self).__init__()
        self.add_argument('-s', '--smp', action='store_true', help='show idle resources on the smp cluster')
        self.add_argument('-g', '--gpu', action='store_true', help='show idle resources on the gpu cluster')
        self.add_argument('-m', '--mpi', action='store_true', help='show idle resources on the mpi cluster')
        self.add_argument('-i', '--invest', action='store_true', help='show idle resources on the invest cluster')
        self.add_argument('-d', '--htc', action='store_true', help='show idle resources on the htc cluster')
        self.add_argument('-p', '--partition', help='Specify non-default partition')

    def print_partition_summary(self, cluster, partition):
        """Print a summary of idle resources in a single partition

        Args:
            cluster: The cluster to print a summary for
            partition: The partition in the parent cluster
        """

        # Use `sinfo` command to determine the status of each node in the given partition
        first_line_of_data = 3
        command = "sinfo -M {0} -p {1} -N -o %N,%C".format(cluster, partition)
        stdout, stderr = Popen(split(command), stdout=PIPE, stderr=PIPE).communicate()
        out = stdout.strip().split()[first_line_of_data:]

        # Count the number of nodes having a given number of idle cores
        core_dict = {}
        for line in out:
            node_name, resource_data = line.split(",")
            _, idle, _, total = [int(x) for x in resource_data.split("/")]

            if idle != 0:
                core_dict.setdefault(idle, 0)
                core_dict[idle] += 1

        # Print results for the current partition
        clus_par_str = "Cluster: {0}, Partition: {1}".format(cluster, partition)
        print(clus_par_str)
        print("=" * len(clus_par_str))

        unit = self.cluster_types[cluster]
        for idle in sorted(core_dict.keys()):
            print("{0:3d} nodes w/ {1:3d} idle {2}".format(core_dict[idle], idle, unit))

        if not core_dict:
            print(" No idle resources")

        print('')

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        # Check which clusters to print idle resources for. Default to all clusters.
        clusters = tuple(clus for clus in self.cluster_partitions if getattr(args, clus))
        if not clusters:
            clusters = tuple(self.cluster_partitions)

        for cluster in clusters:
            partitions_to_print = [args.partition] if args.partition else self.cluster_partitions[cluster]
            for partition in partitions_to_print:
                self.print_partition_summary(cluster, partition)


if __name__ == '__main__':
    CrcIdle().execute()
