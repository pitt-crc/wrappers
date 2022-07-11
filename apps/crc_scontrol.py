"""This file is intended to be temporary. The original application has been
renamed. This placeholder instructs users to use the new command line app.
"""
from .base_parser import BaseParser


class CrcScontrol(BaseParser):
    """The `crc-scontrol` application has been deprecated. Please use the `crc-show-config` application instead."""

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        print(self.__class__.__doc__)
