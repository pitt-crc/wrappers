"""Tests for the ``crc-job-stats`` application."""

from unittest import TestCase
from unittest.mock import patch, Mock
from io import StringIO

from apps.crc_job_stats import CrcJobStats
from tests.fixtures import scontrol_output


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app(cluster: str = 'smp', job_id: str = '99999') -> CrcJobStats:
    """Return a CrcJobStats instance with cluster/job_id set as if inside Slurm."""

    app = CrcJobStats()
    app.cluster = cluster
    app.job_id = job_id
    return app


# ---------------------------------------------------------------------------
# exit_if_not_in_slurm
# ---------------------------------------------------------------------------

class ExitIfNotInSlurm(TestCase):
    """Test that the app exits when not running inside a Slurm job."""

    def test_exits_when_slurm_env_absent(self) -> None:
        """SystemExit is raised when SLURM_JOB_ID is not in the environment."""

        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(SystemExit):
                _make_app().exit_if_not_in_slurm()

    def test_does_not_exit_when_slurm_env_present(self) -> None:
        """No exception is raised when SLURM_JOB_ID is set."""

        with patch.dict('os.environ', {'SLURM_JOB_ID': '99999'}):
            _make_app().exit_if_not_in_slurm()  # must not raise


# ---------------------------------------------------------------------------
# get_job_info — scontrol output parsing
# ---------------------------------------------------------------------------

class GetJobInfo(TestCase):
    """Test parsing of scontrol show job output into a dictionary."""

    @patch('apps.utils.system_info.Shell.run_command')
    def test_returns_dict(self, mock_run: Mock) -> None:
        """get_job_info() returns a dict."""

        mock_run.return_value = scontrol_output.SHOW_JOB
        result = _make_app().get_job_info()
        self.assertIsInstance(result, dict)

    @patch('apps.utils.system_info.Shell.run_command')
    def test_standard_keys_present(self, mock_run: Mock) -> None:
        """All keys required by pretty_print_job_info are present."""

        mock_run.return_value = scontrol_output.SHOW_JOB
        result = _make_app().get_job_info()

        for key in ('JobId', 'SubmitTime', 'EndTime', 'RunTime',
                    'AllocTRES', 'Partition', 'NodeList', 'Command'):
            self.assertIn(key, result, f'Missing expected key: {key}')

    @patch('apps.utils.system_info.Shell.run_command')
    def test_values_parsed_correctly(self, mock_run: Mock) -> None:
        """Key/value pairs are split on the first '=' only."""

        mock_run.return_value = scontrol_output.SHOW_JOB
        result = _make_app().get_job_info()

        self.assertEqual('99999', result['JobId'])
        self.assertEqual('smp', result['Partition'])
        self.assertEqual('node01', result['NodeList'])

    @patch('apps.utils.system_info.Shell.run_command')
    def test_spaced_path_is_repaired(self, mock_run: Mock) -> None:
        """File paths containing whitespace are rejoined correctly."""

        mock_run.return_value = scontrol_output.SHOW_JOB_SPACED_PATH
        result = _make_app().get_job_info()

        # The Command value should contain the escaped space, not be split
        self.assertIn('Command', result)
        self.assertIn('directory', result['Command'])

    @patch('apps.utils.system_info.Shell.run_command')
    def test_command_targets_correct_cluster_and_job(self, mock_run: Mock) -> None:
        """scontrol is called with the correct cluster and job ID."""

        mock_run.return_value = scontrol_output.SHOW_JOB
        _make_app(cluster='gpu', job_id='12345').get_job_info()

        cmd = mock_run.call_args.args[0]
        self.assertIn('-M gpu', cmd)
        self.assertIn('12345', cmd)
        self.assertIn('scontrol', cmd)


# ---------------------------------------------------------------------------
# pretty_print_job_info — output formatting
# ---------------------------------------------------------------------------

class PrettyPrintJobInfo(TestCase):
    """Test the formatted output produced by pretty_print_job_info."""

    def _parse_fixture(self) -> dict:
        """Parse the SHOW_JOB fixture into a dict for use in output tests."""

        with patch('apps.utils.system_info.Shell.run_command',
                   return_value=scontrol_output.SHOW_JOB):
            return _make_app().get_job_info()

    @patch('builtins.print')
    def test_header_printed(self, mock_print: Mock) -> None:
        """A 'JOB STATISTICS' header is printed."""

        _make_app().pretty_print_job_info(self._parse_fixture())
        printed = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('JOB STATISTICS', printed)

    @patch('builtins.print')
    def test_border_printed(self, mock_print: Mock) -> None:
        """A 78-character '=' border is printed."""

        _make_app().pretty_print_job_info(self._parse_fixture())
        mock_print.assert_any_call('=' * 78)

    @patch('builtins.print')
    def test_all_required_fields_printed(self, mock_print: Mock) -> None:
        """All required job fields appear in the output."""

        _make_app().pretty_print_job_info(self._parse_fixture())
        printed = ' '.join(str(c) for c in mock_print.call_args_list)

        for key in ('JobId', 'SubmitTime', 'EndTime', 'RunTime',
                    'AllocTRES', 'Partition', 'NodeList', 'Command'):
            self.assertIn(key, printed, f'Field missing from output: {key}')

    @patch('builtins.print')
    def test_sacct_command_shown(self, mock_print: Mock) -> None:
        """A sacct follow-up command is printed in the footer."""

        _make_app().pretty_print_job_info(self._parse_fixture())
        printed = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('sacct', printed)

    @patch('builtins.print')
    def test_sacct_command_includes_job_id(self, mock_print: Mock) -> None:
        """The sacct command in the footer references the correct job ID."""

        _make_app().pretty_print_job_info(self._parse_fixture())
        printed = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('99999', printed)
