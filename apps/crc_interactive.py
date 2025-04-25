"""A simple wrapper around the Slurm `srun` command.

The application launches users into an interactive Slurm session on a
user-selected cluster and (if specified) partition. Dedicated command line
options for selecting specific clusters.

Each cluster is provided with predefined command line options. As a result,
this application does support dynamic cluster discovery. New clusters need
to be manually added (or removed) by updating the application CLI arguments.
"""

from argparse import ArgumentTypeError, Namespace
from collections import defaultdict
from datetime import time
from os import system

from .utils.cli import BaseParser
from .utils.system_info import Slurm


class CrcInteractive(BaseParser):
    """Launch an interactive Slurm session."""

    min_mpi_nodes = 2  # Minimum limit on requested MPI nodes
    min_mpi_cores = defaultdict(lambda: 28, {'mpi': 48, 'opa-high-mem': 28})  # Minimum cores per MPI partition
    min_time = 1  # Minimum limit on requested time in hours
    max_time = 12  # Maximum limit on requested time in hours
    default_time = time(1)  # Default runtime
    default_nodes = 1  # Default number of nodes
    default_cores = 1  # Default number of requested cores
    default_mpi_cores = 28  # Default number of request cores on an MPI partition
    default_mem = 1  # Default memory in GB
    default_gpus = 0  # Default number of GPUs

    # Clusters names to make available from the command line
    # Maps cluster name to single character abbreviation use in the CLI
    clusters = {
        'smp': 's',
        'gpu': 'g',
        'mpi': 'm',
        'invest': 'i',
        'htc': 'd',
        'teach': 'e'
    }

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super(CrcInteractive, self).__init__()
        self.add_argument(
            '-z', '--print-command', action='store_true',
            help='print the equivalent slurm command and exit')

        # Arguments for specifying what cluster to start an interactive session on
        cluster_args = self.add_argument_group('Cluster Arguments')
        cluster_args.add_argument('-p', '--partition', help='run the session on a specific partition')
        for cluster, abbrev in self.clusters.items():
            cluster_args.add_argument(f'-{abbrev}', f'--{cluster}', action='store_true', help=f'launch a session on the {cluster} cluster')

        # Arguments for requesting additional hardware resources
        resource_args = self.add_argument_group('Arguments for Increased Resources')
        resource_args.add_argument('-b', '--mem', type=int, default=self.default_mem, help='memory in GB')
        resource_args.add_argument(
            '-t', '--time', type=self.parse_time, default=self.default_time,
            help=f'run time in hours or hours:minutes [default: {self.default_time}] ')

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

    @staticmethod
    def parse_time(time_str: str) -> time:
        """Parse a string representation of time in 'HH:MM:SS' format and return a time object.

        Args:
            time_str: A string representing time in 'HH:MM:SS' format.

        Returns:
            time: A time object representing the parsed time.

        Raises:
            ArgumentTypeError: If the input string is not in the correct format or cannot be parsed.
        """

        time_list = time_str.split(':')
        if len(time_list) > 3:
            raise ArgumentTypeError(f'Could not parse time value {time_str}')

        try:
            return time(*map(int, time_list))

        except Exception:
            raise ArgumentTypeError(f'Could not parse time value {time_str}')

    def parse_args(self, args=None, namespace=None) -> Namespace:
        """Parse command line arguments."""

        args = super().parse_args(args, namespace)

        # Set defaults that need to be determined dynamically
        if not args.num_gpus:
            args.num_gpus = 1 if (args.gpu or (args.teach and (args.partition == 'gpu'))) else 0

        # Check wall time is between limits, enable both %H:%M format and integer hours
        check_time = args.time.hour + args.time.minute / 60 + args.time.second / 3600
        if not self.min_time <= check_time <= self.max_time:
            self.error(f'Requested time must be between {self.min_time} and {self.max_time}.')

        # Check the minimum number of nodes are requested for mpi
        if args.mpi and args.num_nodes < self.min_mpi_nodes:
            args.num_nodes = self.min_mpi_nodes
            print(
                 f"You requested less nodes than the minimum required on the MPI cluster. "
                 f"You have now been allocated the minimum of {self.min_mpi_nodes} nodes."
                )
            raise Exception("Less than minimum required mpi nodes specified!")
        # Check the minimum number of cores are requested for mpi
        min_cores = self.min_mpi_cores[args.partition]
        if args.mpi and args.num_cores < min_cores:
            args.num_cores = min_cores
            print(
                  f"You requested less cores than the required number on the MPI cluster. "
                  f"You have now been allocated {min_cores} cores per node on the "
                  f"{args.partition} partition on the MPI cluster."
                )
            raise Exception("Less than minimum required mpi cores specified!")
        # Check a partition is specified if the user is requesting invest
        if args.invest and not args.partition:
            self.error('You must specify a partition when using the invest cluster.')

        return args

    def create_srun_command(self, args: Namespace) -> str:
        """Create an `srun` command based on parsed command line arguments.

        Args:
            args: A dictionary of parsed command line parsed_args.

        Return:
            The equivalent `srun` command as a string.
        """

        # Map arguments from the parent application to equivalent srun arguments
        srun_dict = {
            'partition': '--partition={}',
            'num_nodes': '--nodes={}',
            'time': '--time={}',
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
        if (args.gpu or args.invest or (args.teach and (args.partition == 'gpu'))) and args.num_gpus:
            srun_args += ' ' + f'--gres=gpu:{args.num_gpus}'

        try:
            cluster_to_run = next(cluster for cluster in self.clusters if getattr(args, cluster))

        except StopIteration:
            raise RuntimeError('Please specify which cluster to run on.')

        return f'srun -M {cluster_to_run} {srun_args} --pty bash'

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application.

        Args:
            args: Parsed command line arguments.
        """

        if not any(getattr(args, cluster, False) for cluster in Slurm.get_cluster_names()):
            self.print_help()
            self.exit()

        # Create the slurm command
        srun_command = self.create_srun_command(args)

        if args.print_command:
            print(srun_command)

        else:
            system(srun_command)
