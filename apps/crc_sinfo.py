"""A simple wrapper around the Slurm ``sinfo`` command"""

from .base_parser import BaseParser
from .system_info import Shell


class CrcSinfo(BaseParser):
    """Command line application for fetching data from the Slurm ``sinfo`` utility"""

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        print(Shell.run_command("sinfo -M all"))
