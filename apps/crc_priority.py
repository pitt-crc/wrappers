"""Display the SLURM priority calculation for a given job."""

from argparse import Namespace
from typing import Dict

from apps._base_parser import BaseParser
from apps._system_info import Shell, SlurmInfo


class CrcPriority(BaseParser):
    """Display information about the SLURM priority for a job."""

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcPriority, self).__init__()

        self.add_argument(
            '-j', '--jobid',
            required=True,
            help='print priority calculation for the given job')

        self.add_argument('-M', '--cluster',
                          required=True,
                          help='Use to specify which cluster the job is running on')

    @staticmethod
    def get_priority_info(cluster: str, jobid: str) -> Dict[str, str]:
        """Return a dictionary of SLURM priority values with weights for a given job

        Args:
            cluster: The name of the cluster to get the job on
            jobid: The job ID of the job to get info on

        Returns:
            A dictionary of job priority values fetched from ``sprio``
        """

        sprio_command = f"sprio -M {cluster} -j {jobid}"
        cmd_out = Shell.run_command(sprio_command).split()
        print(cmd_out)
        job_info = {}
        for slurm_option in cmd_out:
            split_values = slurm_option.split(' ')
            job_info[split_values[0]] = split_values[1]

        return job_info

    @staticmethod
    def get_weights_info(cluster: str, jobid: str) -> Dict[str,str]:
        """Return a dictionary of SLURM priority values with weights for a given job

        Args:
            cluster: The name of the cluster to get the job on
            jobid: The job ID of the job to get info on

        Returns:
            A dictionary of job priority weights fetched from ``sprio``
        """

        sprio_command = f"sprio -M {cluster} -j {jobid}"
        cmd_out = Shell.run_command(sprio_command).split()


        sprio_command = f"sprio -M {cluster} -j {jobid}"
        cmd_out = Shell.run_command(sprio_command).split()

        weights_info = {}
        for slurm_option in cmd_out:
            split_values = slurm_option.split(' ')
            job_info[split_values[0]] = split_values[1]

        return weights_info

    def print_priority(self, cluster: str, jobid: str) -> None:
        """Print the SLURM priority information of a given job in a more human readable format

        Args:
            cluster: The name of the cluster
            jobid: The job ID of the job
        """

        priority = self.get_priority_info(cluster, jobid)
        weights = self.get_weights_info(cluster, jobid)

        display = f"""
        Job {jobid} has a priority of {priority['PRIORITY']}. This is a sum of the following factors:\n\n
        Age: {priority['AGE']} * {weights['AGE']} = {priority['AGE'] * weights['AGE']} \n
        Fairshare: {priority['FAIRSHARE']} * {weights['FAIRSHARE']} = {priority['FAIRSHARE'] * weights['FAIRSHARE']} \n
        Job Size: {priority['JOBSIZE']} * {weights['JOBSIZE']} = {priority['JOBSIZE'] * weights['JOBSIZE']} \n
        QOS: {priority['QOS']} * {weights['QOS']} = {priority['QOS'] * weights['QOS']} \n
        """
        print(display)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        If a partition is specified (with or without a cluster name), print a
        summary for that partition.

        Args:
            cluster: The name of the clsuter to get the job on
            jobid: The job ID of the job to get info on
        """

        self.print_priority(args.cluster, args.jobid)

