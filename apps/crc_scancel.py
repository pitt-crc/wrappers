"""Command line application for canceling a Slurm job with a confirmation prompt.

The `crc-scancel` application wraps the Slurm ``scancel`` command and adds an
interactive confirmation step so users can verify they are canceling the correct
job before it is terminated.
"""

import getpass
from argparse import Namespace

from .utils.cli import BaseParser
from .utils.system_info import Shell, Slurm


class CrcScancel(BaseParser):
    """Cancel a Slurm job submitted by the current user."""

    user = getpass.getuser()

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super(CrcScancel, self).__init__()

        # Argument must be a valid integer expressed as a string
        int_as_str = lambda x: str(int(x))
        self.add_argument('job_id', type=int_as_str, help='the job ID to cancel')

    @staticmethod
    def cancel_job_on_cluster(cluster: str, job_id: str) -> None:
        """Cancel a Slurm job on the given cluster.

        Args:
            cluster: The name of the cluster the job is running on.
            job_id: The ID of the Slurm job to cancel.
        """

        Shell.run_command(f'scancel -M {cluster} {job_id}')

    def get_cluster_for_job_id(self, job_id: str) -> Union[str, None]:
        """Return the name of the cluster a given Slurm job is running on.

        Iterates over all known clusters because fetching the cluster directly
        via ``squeue`` fails for scavenger jobs.

        Args:
            job_id: The ID of the Slurm job to locate.

        Returns:
            The cluster name, or None if the job is not found on any cluster.
        """

        # In principle the cluster name can be fetched by running
        #   squeue -h -j job_id
        # However, that approach fails for scavenger jobs. Instead, we iterate
        # over the clusters until we find the right one.

        for cluster in Slurm.get_cluster_names(include_all_clusters=True):
            if job_id in Shell.run_command(f'squeue -h -u {self.user} -j {job_id} -M {cluster}'):
                return cluster

        return None

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application.

        Args:
            args: Parsed command line arguments.
        """

        cluster = self.get_cluster_for_job_id(args.job_id)
        if not cluster:
            self.error(f'Could not find job {args.job_id} running on any known cluster.')

        print(f'Would you like to cancel job {args.job_id} on cluster {cluster}? (y/N): ')
        if Shell.readchar().lower() == 'y':
            self.cancel_job_on_cluster(cluster, args.job_id)
            print(f'Force terminated job {args.job_id}.')
