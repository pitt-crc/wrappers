"""Tests for the ``crc-scancel`` application."""

from unittest import TestCase

from apps.crc_scancel import CrcScancel


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_job_id_is_parsed(self) -> None:
        """Test the job id is recovered from the command line

        This test ensures the correct value is parsed AND the
        value is parsed as a string.
        """

        job_id = '1234'
        args, unknown_args = CrcScancel().parse_known_args([job_id])

        self.assertFalse(unknown_args)
        self.assertEqual(job_id, args.job_id)
