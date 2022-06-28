#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""A simple wrapper around the Slurm ``scancel`` command"""

from os import environ
from sys import stdout

from _base_parser import BaseParser, CommonSettings


class CrcScancel(BaseParser, CommonSettings):
    """Command line application for canceling the user's running slurm jobs"""

    user = environ['USER']

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcScancel, self).__init__()

        # Argument must be a valid integer expressed as a string
        int_as_str = lambda x: str(int(x))
        self.add_argument('job_id', type=int_as_str, help='the job\'s ID')

    def cancel_job_on_cluster(self, cluster, job_id):
        """Cancel a running slurm job

        Args:
            cluster: The name of the cluster the job is running on
            job_id: The ID of the slurm job to cancel
        """

        self.run_command('scancel -M {} {}'.format(cluster, job_id))

    def get_cluster_for_job_id(self, job_id):
        """Return the name of the cluster a slurm job is running on

        Exits the application with an error
        """

        # In principle the cluster name can be fetched by running
        #   squeue -h -j job_id
        # However, that approach fails for scavenger jobs. Instead, we iterate
        # over the clusters until we find the right one.

        for cluster in self.cluster_names:
            # Fetch a list of running slurm jobs matching the username and job id
            command = 'squeue -h -u {} -j job_id -M {}'.format(self.user, cluster)
            if job_id in self.run_command(command):
                return cluster

        return None

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Namespace of parsed arguments from the command line
        """

        cluster = self.get_cluster_for_job_id(args.job_id)
        if not cluster:
            self.error('Could not find job {} running on known clusters'.format(args.job_id))

        stdout.write("Would you like to cancel job {0} on cluster {1}? (y/N): ".format(args.job_id, cluster))
        if self.readchar().lower() == 'y':
            self.cancel_job_on_cluster(cluster, args.job_id)


if __name__ == '__main__':
    CrcScancel().execute()
