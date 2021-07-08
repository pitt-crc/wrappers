#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
""" crc-idle.py -- Find empty cores and GPUs
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


def run_command(command):
    sp = Popen(split(command), stdout=PIPE, stderr=PIPE)
    return sp.communicate()[0].strip().split()


def gpu_based_empty(clus, pars):
    if not isinstance(pars, list):
        pars = [pars]
    for par in pars:
        # Dictionaries to populate
        gpu_counts = {}
        used_counts = {}

        # Generate the GPU counts
        out = run_command("sinfo -M {0} -p {1} -N -o %N,%G".format(clus, par))
        for line in out[3:]:
            name, gpus = line.split(",")
            gpu_counts[name] = int(gpus.split("(")[0].split(":")[-1])

        # Generate the used counts
        out = run_command("squeue -M gpu -p {0} -o %N,%b -t RUNNING".format(par))
        for line in out[3:]:
            sp = line.split(",")
            nodes = sp[:-1]
            count = int(sp[-1].split(":")[-1])

            # There is potentially lists of nodes, e.g. gpu-stage[03-04]
            # -> we can use scontrol show hostname to get this
            fix_nodes = []
            for node in nodes:
                if "[" in node:
                    append_em = run_command("scontrol show hostname {0}".format(node))
                    for add in append_em:
                        fix_nodes.append(add)
                else:
                    fix_nodes.append(node)
            nodes = fix_nodes

            for node in nodes:
                try:
                    used_counts[node] += count
                except:
                    used_counts[node] = count

        # Determine idle GPUs for each machine
        idle_gpus = {}
        for node in gpu_counts.keys():
            try:
                idle_gpus[node] = gpu_counts[node] - used_counts[node]
            except:
                idle_gpus[node] = gpu_counts[node]

        # Reduce idle_gpus into counts
        counts = {}
        counts[0] = 0
        counts[1] = 0
        counts[2] = 0
        counts[3] = 0
        counts[4] = 0
        for v in idle_gpus.values():
            counts[v] += 1

        # Print everything out
        clus_par_str = "Cluster: {0}, Partition: {1}".format(clus, par)
        print(clus_par_str)
        print("=" * len(clus_par_str))
        if counts[0] == len(idle_gpus):
            print(" No idle GPUs")
        else:
            for x in range(1, 5):
                if counts[x] > 0:
                    print("{0:3d} nodes w/ {1:3d} idle GPUs".format(counts[x], x))


def cpu_based_empty_cores(clus, pars):
    if not isinstance(pars, list):
        pars = [pars]

    for par in pars:
        core_dict = {}
        out = run_command("sinfo -M {0} -p {1} -N -o %N,%C".format(clus, par))
        # Generate the core_dict
        for line in out[3:]:
            name, cores = line.split(",")
            _, idle, _, total = [int(x) for x in cores.split("/")]
            if idle != 0 and (idle in core_dict.keys()):
                core_dict[idle] += 1
            elif idle != 0:
                core_dict[idle] = 1

        # Print out the core_dict
        clus_par_str = "Cluster: {0}, Partition: {1}".format(clus, par)
        print(clus_par_str)
        print("=" * len(clus_par_str))
        if len(core_dict.keys()):
            for idle in sorted(core_dict.keys()):
                print("{0:3d} nodes w/ {1:3d} idle cores".format(core_dict[idle], idle))
        else:
            print(" No idle cores")


def cpu_logic(cluster, partition):
    if partition:
        cpu_based_empty_cores(cluster, partition)
    else:
        cpu_based_empty_cores(cluster, CLUSTERS[cluster])


from docopt import docopt
from subprocess import Popen, PIPE
from shlex import split

arguments = docopt(__doc__, version="crc-idle.py version 0.0.1")

CLUSTERS = {
    "smp": ["smp", "high-mem", "legacy"],
    "gpu": ["gtx1080", "titanx", "k40", "v100"],
    "mpi": ["opa", "opa-high-mem", "ib"],
    "htc": ["htc"],
}

# Arguments Check
# ===============
# 1. If no clusters specified, print all clusters
if not any(
    [arguments["--smp"], arguments["--gpu"], arguments["--mpi"], arguments["--htc"]]
):
    arguments["--smp"] = True
    arguments["--gpu"] = True
    arguments["--mpi"] = True
    arguments["--htc"] = True

# 2. If partition is specified, make sure it exists for the cluster
if arguments["--partition"]:
    partition_exists = False
    arguments["--cluster"] = None
    if arguments["--smp"] and arguments["--partition"] in CLUSTERS["smp"]:
        partition_exists = True
        arguments["--cluster"] = "smp"
    elif arguments["--gpu"] and arguments["--partition"] in CLUSTERS["gpu"]:
        partition_exists = True
        arguments["--cluster"] = "gpu"
    elif arguments["--mpi"] and arguments["--partition"] in CLUSTERS["mpi"]:
        partition_exists = True
        arguments["--cluster"] = "mpi"
    elif arguments["--htc"] and arguments["--partition"] in CLUSTERS["htc"]:
        partition_exists = True
        arguments["--cluster"] = "htc"

    if arguments["--cluster"] and not partition_exists:
        exit("Error: Partition {} doesnt exist for cluster {}").format(
            arguments["--partition"], arguments["--cluster"]
        )

if arguments["--smp"]:
    cpu_logic("smp", arguments["--partition"])

if arguments["--gpu"]:
    arguments["--cluster"] = "gpu"
    if arguments["--partition"]:
        gpu_based_empty(arguments["--cluster"], arguments["--partition"])
    else:
        gpu_based_empty(arguments["--cluster"], CLUSTERS[arguments["--cluster"]])

if arguments["--mpi"]:
    cpu_logic("mpi", arguments["--partition"])

if arguments["--htc"]:
    cpu_logic("htc", arguments["--partition"])
