#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""crc-idle.py -- Find empty cores and GPUs
Usage:
    crc-idle.py [-hv]
    crc-idle.py [-hv] (-s | -g | -m | -i | -d) [-p <partition>]

Positional Arguments:
    -s --smp                        Interactive job on smp cluster
    -g --gpu                        Interactive job on gpu cluster
    -m --mpi                        Interactive job on mpi cluster
    -d --htc                        Interactive job on htc cluster

Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-idle.py
    -p --partition <partition>      Use a specific partition
"""

from os.path import basename
from shlex import split
from subprocess import Popen, PIPE

from docopt import docopt

__VERSION__ = '0.2.0'

# Default partitions to print if not specified by user
CLUSTER_PARTITIONS = {
    "smp": ["smp", "high-mem", "legacy"],
    "gpu": ["gtx1080", "titanx", "k40", "v100"],
    "mpi": ["opa", "opa-high-mem", "ib"],
    "htc": ["htc"],
}

# The type of resource available on a cluster
# Either ``cores`` or ``GPUs`` depending on the cluster type
CLUSTER_TYPES = {
    "smp": 'cores',
    "gpu": 'GPUs',
    "mpi": 'cores',
    "htc": 'cores'
}


def print_partition_summary(cluster, partition, unit):
    """Print a summary of idle resources in a single partition

    Args:
        cluster: The cluster to print a summary for
        partition: The partition in the parent cluster
        unit: Either ``cores`` or ``GPUs`` depending on the cluster type
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

    for idle in sorted(core_dict.keys()):
        print("{0:3d} nodes w/ {1:3d} idle {2}\n".format(core_dict[idle], idle, unit))

    if not core_dict:
        print(" No idle resources\n")


if __name__ == '__main__':
    arguments = docopt(__doc__, version='{} version {}'.format(basename(__file__), __VERSION__))

    # Check which clusters to print idle resources for. Default to all clusters.
    clusters = tuple(clus for clus in CLUSTER_PARTITIONS if arguments['--' + clus])
    if not clusters:
        clusters = tuple(CLUSTER_PARTITIONS)

    for cluster in clusters:
        partitions_to_print = [arguments['--partition']] if arguments['--partition'] else CLUSTER_PARTITIONS[cluster]
        for partition in partitions_to_print:
            print_partition_summary(cluster, partition, CLUSTER_TYPES[cluster])
