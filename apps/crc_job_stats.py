"""Command line utility for printing basic information about a running job."""

from os import environ

from ._base_parser import BaseParser
from ._system_info import Shell


class CrcJobStats(BaseParser):
    """Track job information from within a Slurm job.

    Include this command at the end of your Slurm job scripts.
    """

    cluster = environ.get('SLURM_CLUSTER_NAME')
    job_id = environ.get('SLURM_JOB_ID')

    def exit_if_not_in_slurm(self):
        """Exit the application is not running from within a slurm job"""

        if 'SLURM_JOB_ID' not in environ:
            print('This script is meant to be added at the bottom of your Slurm scripts!')
            self.exit()

    def get_job_info(self):
        """Return information about the running job as a dictionary"""

        # Get job information from the ``scontrol`` utility
        # Slurm settings are returned as "key=value" pairs seperated by whitespace
        job_info_command = 'scontrol -M {} show job {}'.format(self.cluster, self.job_id)
        output = Shell.run_command(job_info_command)
        split_output = output.strip().split()

        # Some slurm settings are file paths which may contain whitespace
        # Fix any broken file paths in the split settings values
        drop_indices = []
        for idx, item in enumerate(split_output):
            if '=' not in item:
                drop_indices.append(idx)
                split_output[idx - 1] += r'\ ' + item

        for drop_idx in reversed(sorted(drop_indices)):
            del split_output[drop_idx]

        # Extract the job information as a dictionary
        job_info = {}
        for item in split_output:
            spl = item.split('=', 1)
            job_info[spl[0]] = spl[1]

        return job_info

    def pretty_print_job_info(self, job_info):
        """Print information about a running job in a readable format

        Args:
            job_info: A dictionary of information about the running job
        """

        width = 78
        horizontal_border = '=' * width
        custom_slurm_command = '`sacct -M {} -j {} -S {} -E {}`'.format(
            self.cluster, job_info['JobId'], job_info['SubmitTime'], job_info['EndTime'])

        # Print the output header
        print(horizontal_border)
        print('JOB STATISTICS'.center(width))
        print(horizontal_border)
        print('')

        # Print metrics for running jobs
        for item in ('JobId', 'SubmitTime', 'EndTime', 'RunTime', 'TRES', 'Partition', 'NodeList', 'Command'):
            print('{:>16s}: {}'.format(item, job_info[item]))

        # Add the more information section
        print('')
        print(horizontal_border)
        print(' For more information use the command:')
        print('   - {}'.format(custom_slurm_command))
        print('')
        print(' To control the output of the above command:')
        print('   - Add `--format=<field1,field2,etc>` with fields of interest')
        print('   - See the list of all possible fields by running: `sacct --helpformat`')

        # End the table
        print(horizontal_border)

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        self.exit_if_not_in_slurm()
        job_info = self.get_job_info()
        self.pretty_print_job_info(job_info)
