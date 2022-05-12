#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
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

# Parse command line options and set defaults
arguments = docopt(__doc__, version='crc-interactive.py version 0.0.1')
arguments.setdefault('--time', 1)
arguments.setdefault('--num-nodes', 1)
arguments.setdefault('--num-cores', 1)
arguments.setdefault('--num-gpus', 0)


def check_integer_argument(arguments, key):
    if arguments[key]:
        try:
            return int(arguments[key])

        except ValueError:
            print("WARNING: {0} should have been an integer, setting {0} to 1 hr".format(key))
            return 1

    else:
        return 1


def add_to_srun_args(srun_args, srun_dict, arguments, item):
    if arguments[item]:
        srun_args += ' {} '.format(srun_dict[item]).format(arguments[item])

    return srun_args


def run_command(command, echo=False):
    print(command)
    if echo:
        print(command)

    else:
        return Popen(split(command), stdout=PIPE, stderr=PIPE).communicate()


def run_command_fg(command, echo=False):
    print(command)
    if echo:
        print(command)

    else:
        return Popen(split(command)).communicate()


try:
    # Make sure GPU has default of 1
    if arguments["--gpu"] and arguments["--num-gpus"] == 0:
        arguments["--num-gpus"] = 1

    # Check the integer arguments
    arguments['--time'] = check_integer_argument(arguments, '--time')
    arguments['--num-nodes'] = check_integer_argument(arguments, '--num-nodes')
    arguments['--num-cores'] = check_integer_argument(arguments, '--num-cores')
    arguments['--num-gpus'] = check_integer_argument(arguments, '--num-gpus')
    arguments['--mem'] = check_integer_argument(arguments, '--mem')

    # Check walltime is between limits
    if not (1 <= arguments['--time'] <= 12):
        exit("ERROR: {} is not in 1 <= time <= 12... exiting".format(arguments['--time']))

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
        x11_out, x11_err = run_command("xset q")
        if len(x11_err) == 0:
            srun_args += ' --x11 '

    except OSError:
        pass

    echo = bool(arguments['--print-command'])

    # Run the commands
    if arguments['--smp']:
        run_command_fg("srun -M smp {} --pty bash".format(srun_args), echo)

    elif arguments['--gpu']:
        run_command_fg('srun -M gpu {} --pty bash'.format(srun_args), echo)

    elif arguments['--mpi']:
        if (not arguments['--partition'] == 'compbio') and arguments['--num-nodes'] < 2:
            exit('Error: You must use more than 1 node on the MPI cluster')

        run_command_fg('srun -M mpi {} --pty bash'.format(srun_args), echo)

    elif arguments['--invest']:
        if not arguments['--partition']:
            exit("Error: You must specify a partition when using the Investor cluster")

        run_command_fg('srun -M invest {} --pty bash'.format(srun_args), echo)

    elif arguments['--htc']:
        run_command_fg("srun -M htc {} --pty bash".format(srun_args), echo)

except KeyboardInterrupt:
    exit('Interrupt detected! exiting...')
