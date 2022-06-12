"""Tests for the ``crc-scancel`` application."""

from unittest import TestCase

CrcSCancel = __import__('crc-scancel').CrcSCancel


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_job_id_is_parsed(self):
        """Test the job id is recovered from the command line"""

        job_id = 1234
        args, unknown_args = CrcSCancel().parse_known_args([str(job_id)])

        self.assertFalse(unknown_args)
        self.assertEqual(job_id, args.job_id)
