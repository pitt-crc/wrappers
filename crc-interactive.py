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

from copy import deepcopy
from shlex import split
from subprocess import Popen, PIPE

from docopt import docopt

__VERSION__ = '0.0.2'

# IMPORTANT: Remember to update the module docstring when changing global values

MINIMUM_MPI_NODES = 2  # Minimum limit on requested MPI nodes
MINIMUM_TIME = 1  # Minimum limit on requested time in hours
MAXIMUM_TIME = 12  # Maximum limit on requested time in hours

_arguments = docopt(__doc__, version='{} version {}'.format(__file__, __VERSION__))
DEFAULT_ARGUMENTS = {
    '--time': 1,
    '--num-nodes': 1,
    '--num-cores': 1,
    '--mem': 1,
    '--num-gpus': 1 if _arguments["--gpu"] else 0
}


def set_default_args(arguments, **default_values):
    """Set default values for parsed arguments

    Args:
        arguments: A dictionary of parsed command line arguments
        **default_values: Argument names and their default values

    Returns:
        A copy of the ``arguments`` argument updated with default values
    """

    # Set default value for unspecified arguments
    arguments = deepcopy(arguments)
    for arg_name, default in default_values.items():
        command_line_value = arguments[arg_name]
        arguments.setdefault(arg_name, command_line_value)

        try:
            arguments[arg_name]

        except ValueError:
            print("WARNING: {0} should have been an integer, setting {0} to 1 hr".format(arg_name))
            arguments[arg_name] = default

    return arguments


def validate_arguments(arguments):
    """Exit the application if command-line arguments are invalid

    Args:
        arguments: A dictionary of parsed command line parsed_args
    """

    # Check wall time is between limits
    if not (MINIMUM_TIME <= int(arguments['--time']) <= MAXIMUM_TIME):
        exit("ERROR: {} is not in {} <= time <= {}... exiting".format(arguments['--time'], MINIMUM_TIME, MAXIMUM_TIME))

    if arguments['--mpi'] and (not arguments['--partition'] == 'compbio') and arguments['--num-nodes'] < MINIMUM_MPI_NODES:
        exit('Error: You must use more than 1 node on the MPI cluster')

    if arguments['--invest'] and not arguments['--partition']:
        exit("Error: You must specify a partition when using the Investor cluster")


def run_command(command, stdout=None, stderr=None):
    """Execute a child program in a new process

    Args:
        command: The command to execute in the subprocess
        stdout: Optionally route STDOUT from the child process
        stderr: Optionally route STDERR from the child process

    Returns:
        The submitted child application as a ``Popen`` instance
    """

    return Popen(split(command), stdout=stdout, stderr=stderr).communicate()


def create_srun_command(arguments):
    """Create an ``srun`` command based on parsed commandline arguments

    Args:
        arguments: A dictionary of parsed command line parsed_args

    Return:
        The equivalent ``srun`` command as a string
    """

    # Map arguments from the parent application to equivalent srun arguments
    srun_dict = {
        '--partition': '--partition={}',
        '--num-nodes': '--nodes={}',
        '--time': '--time={}:00:00',
        '--reservation': '--reservation={}',
        '--mem': '--mem={}g',
        '--account': '--account={}',
        '--license': '--licenses={}',
        '--feature': '--constraint={}',
        '--num-gpus': '--gres=gpu:{}',
        "--num-cores": "--cpus-per-task={}" if arguments["--openmp"] else "--ntasks-per-node={}"
    }

    # Build a string of srun arguments
    srun_args = ' --export=ALL'
    for app_arg, srun_arg in srun_dict.items():
        arg_value = arguments[app_arg]
        if arg_value:
            srun_args += ' ' + srun_arg.format(arg_value)

    if (arguments['--gpu'] or arguments['--invest']) and arguments['--num-gpus']:
        srun_args += ' ' + srun_dict['--num-gpus'].format(arguments['--num-gpus'])

    # Add the --x11 flag only if X11 is working
    try:
        x11_out, x11_err = run_command("xset q", stdout=PIPE, stderr=PIPE)
        if not x11_err:
            srun_args += ' --x11 '

    except OSError:
        pass

    cluster_names = ('--smp', '--gpu', '--mpi', '--invest', '--htc')
    cluster_to_run = next(cluster for cluster in cluster_names if arguments.get(cluster))
    return "srun -M {} {} --pty bash".format(cluster_to_run, srun_args)


if __name__ == '__main__':
    _args_with_defaults = set_default_args(_arguments, **DEFAULT_ARGUMENTS)
    validate_arguments(_arguments)
    srun_command = create_srun_command(_arguments)

    if _arguments['--print-command']:
        print(srun_command)
        exit()

    try:
        run_command(srun_command)

    except KeyboardInterrupt:
        exit('Interrupt detected! exiting...')
