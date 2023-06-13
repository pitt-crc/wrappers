"""A simple wrapper around the Slurm ``scancel`` command.

This application allows users to cancel a Slurm job by providing a job ID.
It differs from the default ``scancel`` command by adding a confirmation
prompt to confirm users are canceling the correct job.
"""

import getpass
from argparse import Namespace

from .utils.cli import BaseParser
from .utils.system_info import Shell, Slurm


class CrcScancel(BaseParser):
    """Cancel a Slurm job submitted by the current user."""

    user = getpass.getuser()

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcScancel, self).__init__()

        # Argument must be a valid integer expressed as a string
        int_as_str = lambda x: str(int(x))
        self.add_argument('job_id', type=int_as_str, help='the job ID to cancel')

    @staticmethod
    def cancel_job_on_cluster(cluster: str, job_id: int) -> None:
        """Cancel a running slurm job

        Args:
            cluster: The name of the cluster the job is running on
            job_id: The ID of the slurm job to cancel
        """

        Shell.run_command(f'scancel -M {cluster} {job_id}')

    def get_cluster_for_job_id(self, job_id: int) -> str:
        """Return the name of the cluster a slurm job is running on

        Exits the application with an error

        Args:
            job_id: The ID of th slurm job

        Returns:
            The name of the cluster as a string
        """

        # In principle the cluster name can be fetched by running
        #   squeue -h -j job_id
        # However, that approach fails for scavenger jobs. Instead, we iterate
        # over the clusters until we find the right one.

        for cluster in Slurm.get_cluster_names(include_all_clusters=True):
            # Fetch a list of running slurm jobs matching the username and job id
            command = f'squeue -h -u {self.user} -j {job_id} -M {cluster}'
            if job_id in Shell.run_command(command):
                return cluster

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Namespace of parsed arguments from the command line
        """

        cluster = self.get_cluster_for_job_id(args.job_id)
        if not cluster:
            self.error(f'Could not find job {args.job_id} running on known clusters')

        print(f"Would you like to cancel job {args.job_id} on cluster {cluster}? (y/N): ")
        if Shell.readchar().lower() == 'y':
            self.cancel_job_on_cluster(cluster, args.job_id)
            print(f'Force Terminated job {args.job_id}')
