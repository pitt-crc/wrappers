"""A simple wrapper around the Slurm ``sinfo`` command"""

from ._base_parser import BaseParser
from ._system_info import Shell


class CrcSinfo(BaseParser):
    """Display information about all available Slurm clusters."""

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        print(Shell.run_command("sinfo -M all"))
