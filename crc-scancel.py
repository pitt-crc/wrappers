#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""A simple wrapper around the Slurm ``scancel`` command"""

from os import environ
from subprocess import Popen, PIPE
from sys import stdout

from _base_parser import BaseParser, CommonSettings


class CrcSCancel(BaseParser, CommonSettings):
    """Command line application for canceling the user's running slurm jobs"""

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcSCancel, self).__init__()

        # Argument must be a valid integer expressed as a string
        int_as_str = lambda x: str(int(x))
        self.add_argument('job_id', type=int_as_str, help='the job\'s ID')

    def cancel_job_on_cluster(self, user_name, cluster, job_id):
        """Cancel a running slurm job

        Args:
            user_name: The name of the user who submitted the job
            cluster: The name of the cluster the job is running on
            job_id: The ID of the slurm job to cancel
        """

        # Fetch a list of running slurm jobs matching the username and job id
        process = Popen(['squeue', '-h', '-u', user_name, '-j', job_id, '-M', cluster], stdout=PIPE, stderr=PIPE)
        cmd_out, _ = process.communicate()

        # Verify and cancel the running job
        if job_id in cmd_out:
            stdout.write("Would you like to cancel job {0} on cluster {1}? (y/N): ".format(job_id, cluster))
            if self.readchar().lower() == 'y':
                Popen(['scancel', '-M', cluster, job_id])

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Namespace of parsed arguments from the command line
        """

        user = environ['USER']
        for cluster in self.cluster_partitions:
            self.cancel_job_on_cluster(user, cluster, args.job_id)


if __name__ == '__main__':
    CrcSCancel().execute()
