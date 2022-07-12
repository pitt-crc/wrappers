"""A simple wrapper around the Slurm ``scancel`` command

Command Line Interface
----------------------

.. argparse::
   :nodescription:
   :module: apps.crc_scancel
   :func: CrcScancel
   :prog: crc-scancel
"""

from os import environ
from sys import stdout

from ._base_parser import BaseParser
from ._system_info import Shell, SlurmInfo


class CrcScancel(BaseParser):
    """Cancel a Slurm job submitted by the current user."""

    user = environ['USER']

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcScancel, self).__init__()

        # Argument must be a valid integer expressed as a string
        int_as_str = lambda x: str(int(x))
        self.add_argument('job_id', type=int_as_str, help='the job ID to cancel')

    @staticmethod
    def cancel_job_on_cluster(cluster, job_id):
        """Cancel a running slurm job

        Args:
            cluster: The name of the cluster the job is running on
            job_id: The ID of the slurm job to cancel
        """

        Shell.run_command('scancel -M {} {}'.format(cluster, job_id))

    def get_cluster_for_job_id(self, job_id):
        """Return the name of the cluster a slurm job is running on

        Exits the application with an error
        """

        # In principle the cluster name can be fetched by running
        #   squeue -h -j job_id
        # However, that approach fails for scavenger jobs. Instead, we iterate
        # over the clusters until we find the right one.

        for cluster in SlurmInfo.get_cluster_names(include_all_clusters=True):
            # Fetch a list of running slurm jobs matching the username and job id
            command = 'squeue -h -u {} -j {} -M {}'.format(self.user, job_id, cluster)
            if job_id in Shell.run_command(command):
                return cluster

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Namespace of parsed arguments from the command line
        """

        cluster = self.get_cluster_for_job_id(args.job_id)
        if not cluster:
            self.error('Could not find job {} running on known clusters'.format(args.job_id))

        stdout.write("Would you like to cancel job {0} on cluster {1}? (y/N): ".format(args.job_id, cluster))
        if Shell.readchar().lower() == 'y':
            self.cancel_job_on_cluster(cluster, args.job_id)
            print('Force Terminated job {}'.format(args.job_id))
