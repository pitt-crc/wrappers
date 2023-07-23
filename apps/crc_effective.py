"""Display the effectiveness of recent completed jobs for a given user."""

from argparse import Namespace
import os
from typing import Dict

from .utils.cli import BaseParser
from .utils.system_info import Shell


class CrcEffective(BaseParser):
    """Display the effectiveness of recent completed jobs for a given user."""

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcEffective, self).__init__()

        self.add_argument('-u', '--user',
                          default=os.getlogin(),
                          help='CRC username')

        self.add_argument('-M', '--cluster',
                          required=True,
                          help='Cluster that the job(s) ran on')

        #TODO: Sacct can mess with the slurm database if a sufficiently large time 
        #interval is provided, protect against this somehow?

        self.add_argument('-S', '--starttime',
                          default='midnight',
                          help=f'Show jobs that completed after this date/time (default is midnight')

        self.add_argument('-E', '--endtime',
                          default='now',
                          help=f'Show jobs that completed before this date/time (default is now')

        #TODO: Add logic for supplying a number of jobs to retrieve effectiveness for?
        #self.add_argument('-n', '--num-jobs',
                          #required=False,
                          #type=int,
                          #default=3,
                          #help='Number of completed jobs to display effectiveness for')

    @staticmethod
    def get_job_ids(cluster: str, user: str, startTime: str, endTime: str) -> list[str]:
        """Return a dictionary with order as the key and job ID as the value

        Args:
            cluster: The name of the cluster to get the job on
            user: The user ID to get job info for
            startTime: Date after which to look for jobs
            endTime: Date before which to look for jobs

        Returns:
            A dictionary of job ID  values fetched from ``sacct``
        """

        sacct_command = f"sacct -M {cluster} -S {startTime} -E {endTime} -X -P -n -u {user} -o jobid,state"
        print(f"Your sacct command: {sacct_command}")
        cmd_out = Shell.run_command(sacct_command).split()

        if not cmd_out:
            print(f"ERROR: No jobs on {cluster} completed between {startTime} and {endTime} for {user}")
            exit()

        job_ids = []
        for job in cmd_out:
            split_values = job.split('|')
            job_ids.append(split_values[0])

        return job_ids

    @staticmethod
    def get_seff_info(cluster: str, job_ids: list[str]) -> Dict[str,str]:
        """Return a dictionary of seff output strings

        Args:
            cluster: The name of the cluster to run seff on
            job_ids: The job ID(s) of the jobs to get info on

        Returns:
            A dictionary of job information values provided by ``seff``
        """

        output = []
        for job_id in job_ids:
            #TODO: seff will need to live somewhere where it can have the right permissions
            seff_command = f"/ix/crc/nlc60/github/seff -M {cluster} {job_id}"
            output.append(Shell.run_command(seff_command))

        return output

    def print_effectiveness(self, cluster: str, user: str, startTime: str, endTime: str) -> None:
        """Print the SLURM priority information of a given job in a more human readable format

        Args:
            cluster: The name of the cluster
            jobid: The job ID of the job
        """

        job_ids = self.get_job_ids(cluster, user, startTime, endTime)
        output = self.get_seff_info(cluster,job_ids)

        print(f"Showing jobs on {cluster} that completed between {startTime} and {endTime} for {user}:\n")
        for job in output:
            print(f"{job}\n")

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        If a partition is specified (with or without a cluster name), print a
        summary for that partition.

        Args:
            cluster: The name of the clsuter to get the job on
            jobid: The job ID of the job to get info on
        """

        cluster = args.cluster
        cluster = cluster.lower()
        if cluster == 'gpu':
            print("ERROR: Effectiveness output is currently not provided for jobs running on GPU resource")
            exit()

        #Make sure username is lower-case
        user = args.user.lower()

        self.print_effectiveness(cluster, user, args.starttime, args.endtime)

