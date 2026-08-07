"""Utility classes for interacting with the Slurm scheduler."""

import re
import sys
import termios
import tty
from datetime import date
from shlex import split
from subprocess import PIPE, Popen
from typing import Set, Tuple, Union


class Shell:
    """Methods for interacting with the runtime shell."""

    @staticmethod
    def readchar() -> str:
        """Read a single character from standard input without requiring Enter.

        Returns:
            The character entered by the user.
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

        print()  # Bump terminal onto a new line
        return character

    @staticmethod
    def run_command(command: str, include_err: bool = False) -> Union[str, Tuple[str, str]]:
        """Run a shell command and return its output.

        Args:
            command: The command to execute.
            include_err: Whether to include stderr in the return value.

        Returns:
            The stdout output as a string, or a tuple of (stdout, stderr) if
            `include_err` is True.
        """

        process = Popen(split(command), stdout=PIPE, stderr=PIPE, shell=False)
        std_out, std_err = process.communicate()

        out_decoded = std_out.decode().strip()
        err_decoded = std_err.decode().strip()

        if include_err:
            return out_decoded, err_decoded

        return out_decoded


class Slurm:
    """Methods for querying Slurm cluster and partition configuration."""

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
        'power9',
    }

    @staticmethod
    def is_installed() -> bool:
        """Return whether the Slurm `sacctmgr` command is available on the host.

        Returns:
            True if `sacctmgr` is installed, False otherwise.
        """

        try:
            Shell.run_command('sacctmgr --version')

        except FileNotFoundError:
            return False

        return True

    @classmethod
    def get_cluster_names(cls, include_all_clusters: bool = False) -> Set[str]:
        """Return the names of clusters configured in Slurm.

        Args:
            include_all_clusters: Whether to include clusters listed in
                `ignore_clusters`.

        Returns:
            A set of cluster name strings.
        """

        # Get cluster names using squeue to fetch all running jobs for a non-existent username
        output = Shell.run_command('squeue -u fakeuser -M all')
        cluster_names = set(re.findall(r'CLUSTER: (.*)\n', output))

        if not include_all_clusters:
            cluster_names -= cls.ignore_clusters

        return cluster_names

    @classmethod
    def get_partition_names(cls, cluster_name: str, include_all_partitions: bool = False) -> Set[str]:
        """Return the names of partitions associated with a given cluster.

        Args:
            cluster_name: The name of the Slurm cluster to query.
            include_all_partitions: Whether to include partitions listed in
                `ignore_partitions`.

        Returns:
            A set of partition name strings.
        """

        output = Shell.run_command(f'scontrol -M {cluster_name} show partition')
        partition_names = set(re.findall(r'PartitionName=(.*)\n', output))

        if not include_all_partitions:
            partition_names -= cls.ignore_partitions

        return partition_names

    @classmethod
    def check_slurm_account_exists(cls, account_name: str) -> None:
        """Raise an error if the given Slurm account does not exist.

        Args:
            account_name: The Slurm account name to verify.

        Raises:
            RuntimeError: If no account with the given name is found.
        """

        cmd = f'sacctmgr -n list account account={account_name} format=account%30'
        if not Shell.run_command(cmd):
            raise RuntimeError(f"No Slurm account was found with the name '{account_name}'.")

    @classmethod
    def get_cluster_usage_by_user(cls, account_name: str, start_date: date, cluster: str) -> Union[dict, None]:
        """Return billable usage in hours for a Slurm account, broken down by user.

        Args:
            account_name: The name of the Slurm account to query.
            start_date: The start of the reporting period.
            cluster: The name of the cluster to query usage on.

        Returns:
            A dictionary mapping usernames to usage hours, with a `'total'` key
            for the account-wide sum. Returns None if no data is available.
        """

        cmd = (
            f"sreport -nP cluster accountutilizationbyuser Cluster={cluster} "
            f"Account={account_name} -t Hours Start={start_date.isoformat()} "
            f"-T Billing Format=Proper,Used"
        )

        try:
            data = Shell.run_command(cmd).split('\n')

        except ValueError:
            return None

        if not data or data[0] == '':
            return None

        out_data = {}
        for line in data:
            user, usage = line.split('|')

            # Slurm outputs the total as a value associated with no username
            if user == '':
                out_data['total'] = usage

            else:
                out_data[user] = int(usage)

        return out_data
