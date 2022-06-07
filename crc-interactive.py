#!/usr/bin/python -E
"""A simple wrapper around the Slurm ``srun`` command"""

from shlex import split
from subprocess import Popen, PIPE

from _base_parser import BaseParser, CommonSettings


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


class CrcInteractive(BaseParser, CommonSettings):
    """Commandline utility for launching an interactive slurm session"""

    min_mpi_nodes = 2  # Minimum limit on requested MPI nodes
    min_time = 1  # Minimum limit on requested time in hours
    max_time = 12  # Maximum limit on requested time in hours

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcInteractive, self).__init__()
        self.add_argument('-s', '--smp', action='store_true', help='Interactive job on smp cluster')
        self.add_argument('-g', '--gpu', action='store_true', help='Interactive job on gpu cluster')
        self.add_argument('-m', '--mpi', action='store_true', help='Interactive job on mpi cluster')
        self.add_argument('-i', '--invest', help='Interactive job on invest cluster')
        self.add_argument('-d', '--htc', help='Interactive job on htc cluster')

        self.add_argument('-t', '--time', type=int, default=1, help='Run time in hours [default: 1]')
        self.add_argument('-n', '--num-nodes', type=int, default=1, help='Number of nodes [default: 1]')
        self.add_argument('-p', '--partition', help='Specify non-default partition')
        self.add_argument('-c', '--num-cores', type=int, default=1, help='Number of cores per node [default: 1]')
        self.add_argument('-u', '--num-gpus', type=int, default=0, help='If using -g, the number of GPUs [default: 0]')
        self.add_argument('-r', '--reservation', help='Specify a reservation name')
        self.add_argument('-b', '--mem', type=int, help='Memory in GB')
        self.add_argument('-a', '--account', help='Specify a non-default account')
        self.add_argument('-l', '--license', help='Specify a license')
        self.add_argument('-f', '--feature', help='Specify a feature, e.g. `ti` for GPUs')
        self.add_argument('-z', '--print-command', help='Simply print the command to be run')
        self.add_argument('-o', '--openmp', help='Run using OpenMP style submission')

    def _validate_arguments(self, args):
        """Exit the application if command-line arguments are invalid

        Args:
            args: Parsed commandline arguments
        """

        # Check wall time is between limits
        if not (self.min_time <= args.time <= self.max_time):
            self.error('{} is not in {} <= time <= {}... exiting'.format(args.time, self.min_time, self.max_time))

        # Check the minimum number of nodes are requested for mpi
        if args.mpi and (not args.partition == 'compbio') and args.num_nodes < self.min_mpi_nodes:
            self.error('You must use at least {} nodes when using the MPI cluster'.format(self.min_mpi_nodes))

        # Check a partition is specified if the user is requesting invest
        if args.invest and not args.partition:
            self.error('You must specify a partition when using the Investor cluster')

    @staticmethod
    def x11_is_available():
        """Return whether x11 is available in the current runtime environment"""

        try:
            _, x11_err = run_command('xset q', stdout=PIPE, stderr=PIPE)
            return not x11_err

        except OSError:
            pass

        return False

    def create_srun_command(self, args):
        """Create an ``srun`` command based on parsed commandline arguments

        Args:
            args: A dictionary of parsed command line parsed_args

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
            '--num-cores': '--cpus-per-task={}' if args['--openmp'] else '--ntasks-per-node={}'
        }

        # Build a string of srun arguments
        srun_args = '--export=ALL'
        for app_arg_name, srun_arg_name in srun_dict.items():
            arg_value = getattr(args, app_arg_name)
            if arg_value:
                srun_args += ' ' + srun_arg_name.format(arg_value)

        # The --gres argument in srun needs some special handling so is missing from the above dict
        if (args.gpu or args.invest) and args.num_gpus:
            srun_args += ' ' + '--gres=gpu:{}'.format(args.num_gpus)

        # Add the --x11 flag only if X11 is working
        if self.x11_is_available():
            srun_args += ' --x11 '

        cluster_to_run = next(cluster for cluster in self.cluster_partitions if args.get('--' + cluster))
        return 'srun -M {} {} --pty bash'.format(cluster_to_run, srun_args)

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        # Set defaults that need to be determined dynamically
        if not args.num_gpus:
            args.num_gpus = 1 if args.gpu else 0

        # Create the slurm command
        self._validate_arguments(args)
        srun_command = self.create_srun_command(args)

        if args.print_command:
            print(srun_command)

        else:
            self.run_command(srun_command)


if __name__ == '__main__':
    CrcInteractive().execute()
