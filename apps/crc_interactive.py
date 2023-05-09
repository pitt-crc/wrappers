"""A simple wrapper around the Slurm ``srun`` command

The application launches users into an interactive Slurm session on a
user-selected cluster and (if specified) partition. Dedicated command line
options for selecting specific clusters.

Each cluster is provided with predefined command line options. As a result,
this application does support dynamic cluster discovery. New clusters need
to be manually added (or removed) by updating the application CLI arguments.
"""

from argparse import Namespace
from datetime import datetime
from os import system

from .utils.cli import BaseParser
from .utils.system_info import Slurm


class CrcInteractive(BaseParser):
    """Launch an interactive Slurm session."""

    min_mpi_nodes = 2  # Minimum limit on requested MPI nodes
    min_time = 1  # Minimum limit on requested time in hours
    max_time = 12  # Maximum limit on requested time in hours

    default_time = '1'  # Default runtime
    default_nodes = 1  # Default number of nodes
    default_cores = 1  # Default number of requested cores
    default_mem = 1  # Default memory in GB
    default_gpus = 0  # Default number of GPUs

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super(CrcInteractive, self).__init__()
        self.add_argument(
            '-z', '--print-command', action='store_true',
            help='print the equivalent slurm command and exit')

        # Arguments for specifying what cluster to start an interactive session on
        cluster_args = self.add_argument_group('Cluster Arguments')
        cluster_args.add_argument('-s', '--smp', action='store_true', help='launch a session on the smp cluster')
        cluster_args.add_argument('-g', '--gpu', action='store_true', help='launch a session on the gpu cluster')
        cluster_args.add_argument('-m', '--mpi', action='store_true', help='launch a session on the mpi cluster')
        cluster_args.add_argument('-i', '--invest', action='store_true', help='launch a session on the invest cluster')
        cluster_args.add_argument('-d', '--htc', action='store_true', help='launch a session on the htc cluster')
        cluster_args.add_argument('-e', '--teach', action='store_true', help='launch a session on the teach cluster')
        cluster_args.add_argument('-p', '--partition', help='run the session on a specific partition')

        # Arguments for requesting additional hardware resources
        resource_args = self.add_argument_group('Arguments for Increased Resources')
        resource_args.add_argument('-b', '--mem', type=int, default=self.default_mem, help='memory in GB')
        resource_args.add_argument(
            '-t', '--time', default=self.default_time,
            help=f'run time in hours or hours:minutes [default: {self.default_time}]')

        resource_args.add_argument(
            '-n', '--num-nodes', type=int, default=self.default_nodes,
            help=f'number of nodes [default: {self.default_nodes}]')

        resource_args.add_argument(
            '-c', '--num-cores', type=int, default=self.default_cores,
            help=f'number of cores per node [default: {self.default_cores}]')

        resource_args.add_argument(
            '-u', '--num-gpus', type=int, default=self.default_gpus,
            help=f'if using -g, the number of GPUs [default: {self.default_gpus}]')

        # A grab bag of other settings for configuring slurm jobs
        additional_args = self.add_argument_group('Additional Job Settings')
        additional_args.add_argument('-a', '--account', help='specify a non-default account')
        additional_args.add_argument('-r', '--reservation', help='specify a reservation name')
        additional_args.add_argument('-l', '--license', help='specify a license')
        additional_args.add_argument('-f', '--feature', help='specify a feature, e.g. `ti` for GPUs')
        additional_args.add_argument('-o', '--openmp', action='store_true', help='run using OpenMP style submission')

    def _validate_arguments(self, args: Namespace) -> None:
        """Exit the application if command line arguments are invalid

        Args:
            args: Parsed commandline arguments
        """

        # Check wall time is between limits, enable both %H:%M format and integer hours
        if args.time.isdecimal():
            check_time = int(args.time)
        else:
            check_time = (
                datetime.strptime(args.time, '%H:%M').hour +
                datetime.strptime(args.time, '%H:%M').minute / 60)

        if not self.min_time <= check_time <= self.max_time:
            self.error(f'{check_time} is not in {self.min_time} <= time <= {self.max_time}... exiting')

        # Check the minimum number of nodes are requested for mpi
        if args.mpi and (not args.partition == 'compbio') and args.num_nodes < self.min_mpi_nodes:
            self.error(f'You must use at least {self.min_mpi_nodes} nodes when using the MPI cluster')

        # Check a partition is specified if the user is requesting invest
        if args.invest and not args.partition:
            self.error('You must specify a partition when using the Investor cluster')

    def create_srun_command(self, args: Namespace) -> str:
        """Create an ``srun`` command based on parsed command line arguments

        Args:
            args: A dictionary of parsed command line parsed_args

        Return:
            The equivalent ``srun`` command as a string
        """

        # Map arguments from the parent application to equivalent srun arguments
        srun_dict = {
            'partition': '--partition={}',
            'num_nodes': '--nodes={}',
            'time': '--time={}:00',
            'reservation': '--reservation={}',
            'mem': '--mem={}g',
            'account': '--account={}',
            'license': '--licenses={}',
            'feature': '--constraint={}',
            'num_cores': '--cpus-per-task={}' if getattr(args, 'openmp') else '--ntasks-per-node={}'
        }

        # Build a string of srun arguments
        srun_args = '--export=ALL'

        for app_arg_name, srun_arg_name in srun_dict.items():
            arg_value = getattr(args, app_arg_name)
            if arg_value:
                srun_args += ' ' + srun_arg_name.format(arg_value)

        # The --gres argument in srun needs some special handling so is missing from the above dict
        if (args.gpu or args.invest) and args.num_gpus:
            srun_args += ' ' + f'--gres=gpu:{args.num_gpus}'

        cluster_to_run = next(cluster for cluster in Slurm.get_cluster_names() if getattr(args, cluster))
        return f'srun -M {cluster_to_run} {srun_args} --pty bash'

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        if not any(getattr(args, cluster, False) for cluster in Slurm.get_cluster_names()):
            self.print_help()
            self.exit()

        # Set defaults that need to be determined dynamically
        if not args.num_gpus:
            args.num_gpus = 1 if args.gpu else 0

        # Create the slurm command
        self._validate_arguments(args)
        srun_command = self.create_srun_command(args)

        if args.print_command:
            print(srun_command)

        else:
            system(srun_command)
