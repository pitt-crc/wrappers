#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""Find empty cores and GPUs"""

from argparse import ArgumentParser

from shlex import split
from subprocess import Popen, PIPE

__version__ = '0.1.0'
CLUSTER_PARTITIONS = {
    "smp": ["smp", "high-mem", "legacy"],
    "gpu": ["gtx1080", "titanx", "k40", "v100"],
    "mpi": ["opa", "opa-high-mem", "ib"],
    "htc": ["htc"],
}


class App(ArgumentParser):
    """Command line application for listing idle CPU and GPU resources"""

    def __init__(self):
        """Define the application CLI"""

        super(App, self).__init__()
        self.add_argument('-s', '--smp', action='store_true', help='Interactive job on smp cluster')
        self.add_argument('-g', '--gpu', action='store_true', help='Interactive job on gpu cluster')
        self.add_argument('-m', '--mpi', action='store_true', help='Interactive job on mpi cluster')
        self.add_argument('-d', '--htc', action='store_true', help='Interactive job on htc cluster')

        self.add_argument('-p', '--partition', help='Use a specific partition')

    @staticmethod
    def print_partition_summary(cluster, partition):
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
            num_idle_cores = int(resource_data.split("/")[1])

            if num_idle_cores != 0:
                core_dict.setdefault(num_idle_cores, 0)
                core_dict[num_idle_cores] += 1

        # Print results for the current partition
        clus_par_str = "Cluster: {0}, Partition: {1}".format(cluster, partition)
        print(clus_par_str)
        print("=" * len(clus_par_str))

        for idle in sorted(core_dict.keys()):
            print("{0:3d} nodes w/ {1:3d} idle {2}".format(core_dict[idle], idle, RESOURCE_TYPES[cluster]))

        if not core_dict:
            print(" No idle resources")

        print('')

    def run(self):
        """Parse command line arguments and execute application"""

        args = self.parse_args()

        # Check which clusters to print idle resources for. Default to all clusters.
        clusters = tuple(clus for clus in CLUSTER_PARTITIONS if getattr(args, clus))
        if not clusters:
            clusters = tuple(CLUSTER_PARTITIONS)

        # Check if we need to print for a single partition
        if args.partition:
            if len(clusters) > 1:
                exit("You cannot request a partition when specifying multiple clusters")

            elif args.partition not in CLUSTER_PARTITIONS[clusters[0]]:
                exit("Error: Partition {} doesnt exist for cluster {}".format(args.partition, clusters[0]))

        for cluster in clusters:
            partitions_to_print = [args.partition] if args.partition else CLUSTER_PARTITIONS[cluster]
            for partition in partitions_to_print:
                self.print_partition_summary(cluster, partition)


if __name__ == '__main__':
    App().run()
