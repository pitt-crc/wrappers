#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
from os import environ

from _base_parser import BaseParser


class CrcJobStats(BaseParser):
    """A commandline tool for tracking job information from with a Slurm job"""

    cluster = environ.get('SLURM_CLUSTER_NAME')
    job_id = environ.get('SLURM_JOB_ID')

    def exit_if_not_in_slurm(self):
        """Error if the application is not running from within a slurm job"""

        if 'SLURM_JOB_ID' not in environ:
            print('This script is meant to be added at the bottom of your Slurm scripts!')
            self.exit()

    def get_job_info(self):
        """Return information about the running job as a dictionary"""

        # Get job information from the ``scontrol`` utility
        output = self.run_command(['scontrol', '-M', self.cluster, 'show', 'job', self.job_id])
        split_output = output.strip().split()

        # Need to deal with spaces in directory names
        drop_indices = []
        for idx, item in enumerate(split_output):
            if '=' not in item:
                drop_indices.append(idx)
                split_output[idx - 1] += '\ ' + item

        for drop_idx in reversed(sorted(drop_indices)):
            del split_output[drop_idx]

        # Extract the job information
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

        # Print the output header
        width = 78
        print('=' * width)
        print('JOB STATISTICS'.center(width))
        print('=' * width)
        print('')

        # Print metrics for running jobs
        for item in ('SubmitTime', 'EndTime', 'RunTime', 'JobId', 'TRES', 'Partition', 'NodeList', 'Command'):
            print('{:>16s}: {}'.format(item, job_info[item]))

        # Add the more information section
        print('')
        print('=' * width)
        print(' For more information use the command:')
        print('   - `sacct -M {} -j {} -S {} -E {}`'.format(environ['SLURM_CLUSTER_NAME'], job_info['JobId'], job_info['SubmitTime'], job_info['EndTime']))
        print('')
        print(' To control the output of the bove command:')
        print('   - Add `--format=<field1,field2,etc>` with fields of interest')
        print('   - See the list of all possible fields by running: `sacct --helpformat`')

        # End the table
        print('=' * width)

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        self.exit_if_not_in_slurm()
        job_info = self.get_job_info()
        self.pretty_print_job_info(job_info)


if __name__ == '__main__':
    CrcJobStats().execute()
