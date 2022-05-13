#!/usr/bin/python
"""crc-interactive.py -- An interactive Slurm helper
Usage:
    crc-interactive.py (-s | -g | -m | -i | -d) [-hvzo] [-t <time>] [-n <num-nodes>]
        [-p <partition>] [-c <num-cores>] [-u <num-gpus>] [-r <res-name>]
        [-b <memory>] [-a <account>] [-l <license>] [-f <feature>]

Positional Arguments:
    -s --smp                        Interactive job on smp cluster
    -g --gpu                        Interactive job on gpu cluster
    -m --mpi                        Interactive job on mpi cluster
    -i --invest                     Interactive job on invest cluster
    -d --htc                        Interactive job on htc cluster
Options:
    -h --help                       Print this screen and exit
    -v --version                    Print the version of crc-interactive.py
    -t --time <time>                Run time in hours, 1 <= time <= 12 [default: 1]
    -n --num-nodes <num-nodes>      Number of nodes [default: 1]
    -p --partition <partition>      Specify non-default partition
    -c --num-cores <num-cores>      Number of cores per node [default: 1]
    -u --num-gpus <num-gpus>        Used with -g only, number of GPUs [default: 0]
    -r --reservation <res-name>     Specify a reservation name
    -b --mem <memory>               Memory in GB
    -a --account <account>          Specify a non-default account
    -l --license <license>          Specify a license
    -f --feature <feature>          Specify a feature, e.g. `ti` for GPUs
    -z --print-command              Simply print the command to be run
    -o --openmp                     Run using OpenMP style submission
"""

from shlex import split
from subprocess import Popen, PIPE

from docopt import docopt

__VERSION__ = '0.0.2'
MINIMUM_MPI_NODES = 2


def parse_args():
    """Parse arguments from the command line and return them as a dictionary

    Includes default values for any unspecified values

    Returns:
        A dictionary of parsed arguments from the command line
    """

    arguments = docopt(__doc__, version='{} version {}'.format(__file__, __VERSION__))

    # Set default values
    arguments.setdefault('--time', 1)
    arguments.setdefault('--num-nodes', 1)
    arguments.setdefault('--num-cores', 1)
    arguments.setdefault('--time', 1)
    arguments.setdefault('--num-nodes', 1)
    arguments.setdefault('--num-cores', 1)
    arguments.setdefault('--mem', 1)
    if arguments["--gpu"]:
        arguments.setdefault('--num-gpus', 1)

    else:
        arguments.setdefault('--num-gpus', 0)

    # This is here to maintain the same behavior as older application versions
    for key in ['--time', '--num-nodes', '--num-cores', '--num-gpus', '--mem']:
        try:
            int(arguments[key])

        except ValueError:
            print("WARNING: {0} should have been an integer, setting {0} to 1 hr".format(key))
            arguments[key] = 1

    return arguments


def validate_arguments(arguments):
    """Exit the application if command-line arguments are invalid

    Args:
        arguments: A dictionary of parsed command line arguments
    """

    # Check wall time is between limits
    if not (1 <= arguments['--time'] <= 12):
        exit("ERROR: {} is not in 1 <= time <= 12... exiting".format(arguments['--time']))

    if arguments['--mpi'] and (not arguments['--partition'] == 'compbio') and arguments['--num-nodes'] < MINIMUM_MPI_NODES:
        exit('Error: You must use more than 1 node on the MPI cluster')

    if arguments['--invest'] and not arguments['--partition']:
        exit("Error: You must specify a partition when using the Investor cluster")


def add_to_srun_args(srun_args, srun_dict, arguments, item):
    if arguments[item]:
        srun_args += ' {} '.format(srun_dict[item]).format(arguments[item])

    return srun_args


def run_command(command, stdout=None, stderr=None):
    return Popen(split(command), stdout=stdout, stderr=stderr).communicate()


def create_srun_command(arguments):
    # Build up the srun arguments
    srun_dict = {'--partition': '--partition={}', '--num-nodes': '--nodes={}',
                 '--time': '--time={}:00:00', '--reservation': '--reservation={}', '--num-gpus': '--gres=gpu:{}',
                 '--mem': '--mem={}g', '--account': '--account={}', '--license': '--licenses={}',
                 '--feature': '--constraint={}'}

    if arguments["--openmp"]:
        srun_dict["--num-cores"] = "--cpus-per-task={}"

    else:
        srun_dict["--num-cores"] = "--ntasks-per-node={}"

    srun_args = ""
    srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--partition')
    srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--num-nodes')
    srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--num-cores')
    srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--time')
    srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--reservation')
    srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--mem')
    srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--account')

    if arguments['--gpu'] or arguments['--invest']:
        srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--num-gpus')

    if arguments['--license']:
        srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--license')

    if arguments['--feature']:
        srun_args = add_to_srun_args(srun_args, srun_dict, arguments, '--feature')

    # Export MODULEPATH
    srun_args += ' --export=ALL '

    # Add --x11 flag?
    try:
        x11_out, x11_err = run_command("xset q", stdout=PIPE, stderr=PIPE)
        if len(x11_err) == 0:
            srun_args += ' --x11 '

    except OSError:
        pass

    cluster_names = ('smp', 'gpu', 'mpi', 'invest', 'htc')
    cluster_to_run = next(cluster for cluster in cluster_names if arguments[cluster])
    return "srun -M {} {} --pty bash".format(cluster_to_run, srun_args)


if __name__ == '__main__':
    _arguments = parse_args()
    validate_arguments(_arguments)
    srun_command = create_srun_command(_arguments)

    if _arguments['--print-command']:
        print(srun_command)
        exit()

    try:
        run_command(srun_command)

    except KeyboardInterrupt:
        exit('Interrupt detected! exiting...')
