"""Utility class for fetching data and interacting with the parent system."""

from datetime import date
import re
from shlex import split
from subprocess import PIPE, Popen
import sys
import termios
import tty
from typing import Set, Tuple, Union


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

        print()  # Bump terminal onto a new line
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


class Slurm:
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

    @staticmethod
    def is_installed() -> bool:
        """Return whether ``sacctmgr`` is installed on the host machine"""

        try:
            Shell.run_command('sacctmgr --version')

        except FileNotFoundError:
            return False

        return True

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

    @classmethod
    def check_slurm_account_exists(cls, account_name: str) -> None:
        """Check if the provided slurm account exists"""

        cmd = f'sacctmgr -n list account account={account_name} format=account%30'
        account_exists = Shell.run_command(cmd)
        if not account_exists:
            raise RuntimeError(f"No Slurm account was found with the name '{account_name}'.")

    @classmethod
    def get_cluster_usage_by_user(cls, account_name: str, start_date: date, cluster: str) -> int:
        """Return the total billable usage in hours for a given Slurm account

        Args:
            account_name: The name of the account to get usage for
            cluster: The name of the cluster to get usage on

        Returns:
            An integer representing the total (historical + current) billing TRES hours usage from sshare
        """

        start = start_date.isoformat()
        cmd = f"sreport -nP cluster accountutilizationbyuser Cluster={cluster} Account={account_name} -t Hours Start={start} -T Billing Format=Proper,Used"

        try:
            total, *data = Shell.run_command(cmd).split('\n')
        except ValueError:
            return None

        if not data:
            return None

        out_data = dict()
        out_data['total'] = total.strip('|')
        for line in data:
            user, usage = line.split('|')
            usage = int(usage)
            out_data[user] = usage

        return out_data


