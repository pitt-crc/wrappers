import sys
import termios
import tty
from shlex import split
from subprocess import Popen, PIPE


class CommonSettings(object):
    """Parent class for adding common settings to a command line application"""

    banking_db_path = 'sqlite:////ihome/crc/bank/crc_bank.db'
    cluster_names = ('smp', 'gpu', 'mpi', 'htc')


class Shell:
    """Methods for interacting with the runtime shell"""

    @staticmethod
    def readchar():
        """Read a single character from the command line"""

        # Get the current settings of the standard input file descriptor
        file_descriptor = sys.stdin.fileno()
        old_settings = termios.tcgetattr(file_descriptor)

        try:
            tty.setraw(sys.stdin.fileno())
            character = sys.stdin.read(1)

        finally:
            # Restore the original standard input settings
            termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)

        print('')
        return character

    @staticmethod
    def run_command(command, include_err=False):
        """Run a command in a dedicated shell

        Args:
            command: The command to execute as a string
            include_err: Include output to stderr in the returned values

        Returns:
            The output to stdout and (optionally) stderr
        """

        command_list = split(command)
        process = Popen(command_list, stdout=PIPE, stderr=PIPE, shell=False)
        std_out, std_err = process.communicate()
        if include_err:
            return std_out.strip(), std_err.strip()

        return std_out.strip()
