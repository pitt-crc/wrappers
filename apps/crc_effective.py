"""Display the effectiveness of recent completed jobs for a given user."""

from argparse import Namespace
from typing import Dict

from .utils.cli import BaseParser
from .utils.system_info import Shell


class CrcEffective(BaseParser):
    """Display the effectiveness of recent completed jobs for a given user."""

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcEffective, self).__init__()

        self.add_argument('-u', '--user',
                          required=True,
                          help='User to check job effectiveness for')

        self.add_argument('-M', '--cluster',
                          required=True,
                          help='Cluster the jobs ran on')

        #TODO: Add logic for supplying a time interval to find jobs between

        #TODO: Add logic for supplying a number of jobs to retrieve effectiveness for?
        #self.add_argument('-n', '--num-jobs',
                          #required=False,
                          #type=int,
                          #default=3,
                          #help='Number of completed jobs to display effectiveness for')

    @staticmethod
    def get_job_ids(cluster: str, user: str) -> list[str]:
        """Return a dictionary with order as the key and job ID as the value

        Args:
            cluster: The name of the cluster to get the job on
            user: The user ID to get job info for

        Returns:
            A dictionary of job ID  values fetched from ``sacct``
        """

        sacct_command = f"sacct -M {cluster} -X -P -n -u {user} -o jobid,state"
        cmd_out = Shell.run_command(sacct_command).split()

        if not cmd_out:
            print(f"ERROR: No recently completed jobs found on {cluster} for {user}")
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

        #TODO ssh to head node?

        output = []
        for job_id in job_ids:
            seff_command = f"/ix/crc/nlc60/github/seff -M {cluster} {job_id}"
            output.append(Shell.run_command(seff_command))

        return output

    def print_effectiveness(self, cluster: str, user: str) -> None:
        """Print the SLURM priority information of a given job in a more human readable format

        Args:
            cluster: The name of the cluster
            jobid: The job ID of the job
        """

        job_ids = self.get_job_ids(cluster, user)
        output = self.get_seff_info(cluster,job_ids)

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

        user = args.user
        user = user.lower()

        self.print_effectiveness(cluster, user)

