"""Command line utility for printing statistics about a running Slurm job.

The `crc-job-stats` application is intended to be called at the end of a Slurm
job submission script. It uses `scontrol` to fetch job metadata and prints a
formatted summary to the terminal.
"""

from argparse import Namespace
from os import environ

from .utils.cli import BaseParser
from .utils.system_info import Shell


class CrcJobStats(BaseParser):
    """Display statistics for the currently running Slurm job.

    Include this command at the end of your Slurm job scripts.
    """

    cluster = environ.get('SLURM_CLUSTER_NAME')
    job_id = environ.get('SLURM_JOB_ID')

    def exit_if_not_in_slurm(self) -> None:
        """Exit the application if not running inside a Slurm job."""

        if 'SLURM_JOB_ID' not in environ:
            print('This script is meant to be added at the bottom of your Slurm scripts!')
            self.exit()

    def get_job_info(self) -> dict[str, str]:
        """Return metadata for the current job as a dictionary.

        Parses `scontrol` output into key/value pairs, handling file paths
        that may contain whitespace.

        Returns:
            A dictionary of Slurm job settings fetched from `scontrol`.
        """

        # Get job information from the `scontrol` utility
        # Slurm settings are returned as "key=value" pairs seperated by whitespace
        output = Shell.run_command(f'scontrol -M {self.cluster} show job {self.job_id}')
        split_output = output.strip().split()

        # Some slurm settings are file paths which may contain whitespace
        # Fix any broken file paths in the split output values
        drop_indices = []
        for idx, item in enumerate(split_output):
            if '=' not in item:
                drop_indices.append(idx)
                split_output[idx - 1] += r'\ ' + item

        for idx in reversed(sorted(drop_indices)):
            del split_output[idx]

        # Extract the job information as a dictionary
        return {k: v for item in split_output for k, v in [item.split('=', 1)]}

    def pretty_print_job_info(self, job_info: dict[str, str]) -> None:
        """Print a formatted summary of job metadata to the terminal.

        Args:
            job_info: A dictionary of Slurm job settings from `scontrol`.
        """

        width = 78
        border = '=' * width
        sacct_cmd = '`sacct -M {} -j {} -S {} -E {}`'.format(
            self.cluster,
            job_info['JobId'],
            job_info['SubmitTime'],
            job_info['EndTime']
        )

        # Print the output header
        print(border)
        print('JOB STATISTICS'.center(width))
        print(border)
        print('')

        # Print metrics for running jobs
        for key in ('JobId', 'SubmitTime', 'EndTime', 'RunTime', 'AllocTRES', 'Partition', 'NodeList', 'Command'):
            print(f'{key:>16s}: {job_info[key]}')

        # Add the more information section
        print('')
        print(border)
        print(' For more information use the command:')
        print(f'   - {sacct_cmd}')
        print('')
        print(' To control the output of the above command:')
        print('   - Add `--format=<field1,field2,etc>` with fields of interest')
        print('   - See the list of all possible fields by running: `sacct --helpformat`')
        print(border)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application.

        Args:
            args: Parsed command line arguments.
        """

        self.exit_if_not_in_slurm()
        job_info = self.get_job_info()
        self.pretty_print_job_info(job_info)
