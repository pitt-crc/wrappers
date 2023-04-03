"""Utility class for fetching data and interacting with the parent system."""

import re
import sys
import termios
import tty
from shlex import split
from subprocess import Popen, PIPE
from typing import Union, Tuple, Set


class Shell:
    """Methods for interacting with the runtime shell."""

    @staticmethod
    def readchar() -> str:
        """Read a single character from the command line

        Returns:
            The character entered by the user
        """

        # Get the current settings of the standard input file descriptor
        file_descriptor = sys.stdin.fileno()
        old_settings = termios.tcgetattr(file_descriptor)

        try:
            tty.setraw(sys.stdin.fileno())
            character = sys.stdin.read(1)

        finally:
            # Restore the original standard input settings
            termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)

        print('')  # Bump terminal onto a new line
        return character

    @staticmethod
    def run_command(command: str, include_err: bool = False) -> Union[str, Tuple[str, str]]:
        """Run a command in a dedicated shell

        Args:
            command: The command to execute as a string
            include_err: Include output to stderr in the returned values

        Returns:
            The output to stdout and (optionally) stderr
        """

        command_list = split(command)
        process = Popen(command_list, stdout=PIPE, stderr=PIPE, shell=False)
        std_out, std_err = process.communicate()
        out_decoded = std_out.decode().strip()
        err_decoded = std_err.decode().strip()

        if include_err:
            return out_decoded, err_decoded

        return out_decoded


class SlurmInfo:
    """Class for fetching Slurm config data."""

    ignore_clusters = {'azure'}
    ignore_partitions = {
        'pliu',
        'jdurrant',
        'kjordan',
        'lchong',
        'eschneider',
        'eschneider-mpi',
        'isenocak',
        'isenocak-mpi',
        'power9'
    }

    @classmethod
    def get_cluster_names(cls, include_all_clusters: bool = False) -> Set[str]:
        """Return cluster names configured with slurm

        Args:
            include_all_clusters: Include clusters that are otherwise marked as ignored

        Returns:
            A set of cluster names
        """

        # Get cluster names using squeue to fetch all running jobs for a non-existent username
        output = Shell.run_command('squeue -u fakeuser -M all')
        regex_pattern = re.compile(r'CLUSTER: (.*)\n')
        cluster_names = set(re.findall(regex_pattern, output))

        if not include_all_clusters:
            cluster_names -= cls.ignore_clusters

        return cluster_names

    @classmethod
    def get_partition_names(cls, cluster_name: str, include_all_partitions: bool = False) -> Set[str]:
        """Return a tuple of partition names associated with a given slurm cluster

        Args:
            cluster_name: The name of a slurm cluster
            include_all_partitions: Include partitions that are otherwise marked as ignored

        Returns:
            A set of partition names
        """

        output = Shell.run_command("scontrol -M {} show partition".format(cluster_name))
        regex_pattern = re.compile(r'PartitionName=(.*)\n')
        partition_names = set(re.findall(regex_pattern, output))

        if not include_all_partitions:
            partition_names -= cls.ignore_partitions

        return partition_names
