"""Tests for the ``crc-usage`` application."""

import grp
import os
from datetime import date
from unittest import TestCase, skipIf, mock
from unittest.mock import patch, Mock

from apps.crc_usage import CrcUsage
from apps.utils.system_info import Slurm


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments."""

    def test_default_account_is_primary_group(self) -> None:
        """Account defaults to the current user's primary group."""

        parsed = CrcUsage().parse_args([]).account
        self.assertEqual(grp.getgrgid(os.getgid()).gr_name, parsed)

    def test_custom_account_stored(self) -> None:
        """An explicitly provided account name is stored."""

        self.assertEqual('dummy_account', CrcUsage().parse_args(['dummy_account']).account)

    def test_unknown_args_empty_for_valid_input(self) -> None:
        _, unknown = CrcUsage().parse_known_args(['my_account'])
        self.assertFalse(unknown)


# ---------------------------------------------------------------------------
# print_summary_table
# ---------------------------------------------------------------------------

class PrintSummaryTable(TestCase):
    """Test the allocation request summary table."""

    def setUp(self) -> None:
        self.account = 'test_account'
        self.requests = [
            {'id': 1, 'title': 'Request 1', 'expire': '2023-12-31'},
            {'id': 2, 'title': 'Request 2', 'expire': '2024-12-31'},
        ]
        self.per_request_totals = {
            1: {'cluster1': 1000, 'cluster2': 2000},
            2: {'cluster1': 1500, 'cluster2': 2500},
        }

    def _capture_output(self) -> str:
        with mock.patch('builtins.print') as mock_print:
            CrcUsage.print_summary_table(self.requests, self.account, self.per_request_totals)
            return '\n'.join(str(c.args[0]) for c in mock_print.call_args_list)

    def test_table_is_printed(self) -> None:
        """print() is called at least once."""

        with mock.patch('builtins.print') as mock_print:
            CrcUsage.print_summary_table(self.requests, self.account, self.per_request_totals)
            self.assertTrue(mock_print.called)

    def test_account_name_in_title(self) -> None:
        self.assertIn("test_account", self._capture_output())

    def test_required_column_headers_present(self) -> None:
        output = self._capture_output()
        for header in ('ID', 'TITLE', 'EXPIRATION DATE', 'CLUSTER', 'SERVICE UNITS'):
            self.assertIn(header, output)

    def test_request_data_present(self) -> None:
        output = self._capture_output()
        self.assertIn('Request 1', output)
        self.assertIn('2023-12-31', output)
        self.assertIn('Request 2', output)
        self.assertIn('2024-12-31', output)

    def test_cluster_and_su_data_present(self) -> None:
        output = self._capture_output()
        self.assertIn('cluster1', output)
        self.assertIn('1000', output)
        self.assertIn('cluster2', output)
        self.assertIn('2500', output)

    def test_all_request_ids_present(self) -> None:
        output = self._capture_output()
        self.assertIn('1', output)
        self.assertIn('2', output)

    def test_empty_requests_list_does_not_raise(self) -> None:
        """An empty allocation list prints without error."""

        with mock.patch('builtins.print'):
            CrcUsage.print_summary_table([], self.account, {})


# ---------------------------------------------------------------------------
# print_usage_table
# ---------------------------------------------------------------------------

class PrintUsageTable(TestCase):
    """Test the per-user consumption summary table."""

    def setUp(self) -> None:
        self.account = 'test_account'
        self.awarded = {'cluster1': 1000, 'cluster2': 2000}
        self.start_date = date(2023, 1, 1)

    def _capture_output_with_usage(self, usage_data) -> str:
        with mock.patch('apps.utils.system_info.Slurm.get_cluster_usage_by_user',
                        return_value=usage_data):
            with mock.patch('builtins.print') as mock_print:
                CrcUsage.print_usage_table(self.account, self.awarded, self.start_date)
                return '\n'.join(str(c.args[0]) for c in mock_print.call_args_list)

    def test_table_is_printed(self) -> None:
        with mock.patch('apps.utils.system_info.Slurm.get_cluster_usage_by_user',
                        return_value=None):
            with mock.patch('builtins.print') as mock_print:
                CrcUsage.print_usage_table(self.account, self.awarded, self.start_date)
                self.assertTrue(mock_print.called)

    def test_usage_values_present(self) -> None:
        output = self._capture_output_with_usage({'user1': 100, 'user2': 200, 'total': 300})
        self.assertIn('TOTAL USED: 300', output)
        self.assertIn('AWARDED: 1000', output)
        self.assertIn('user1', output)
        self.assertIn('user2', output)

    def test_percent_used_calculated(self) -> None:
        # 300 / 1000 = 30%
        output = self._capture_output_with_usage({'user1': 300, 'total': 300})
        self.assertIn('% USED: 30', output)

    def test_no_usage_data_shows_zeros(self) -> None:
        output = self._capture_output_with_usage(None)
        self.assertIn('TOTAL USED: 0', output)
        self.assertIn('% USED: 0', output)

    def test_both_clusters_reported(self) -> None:
        """Each awarded cluster gets a row in the table."""

        output = self._capture_output_with_usage({'user1': 100, 'total': 100})
        self.assertIn('cluster1', output)
        self.assertIn('cluster2', output)

    def test_usage_query_includes_account_and_start_date(self) -> None:
        """Slurm is queried with the correct account and start date."""

        with mock.patch('apps.utils.system_info.Slurm.get_cluster_usage_by_user',
                        return_value=None) as mock_usage:
            with mock.patch('builtins.print'):
                CrcUsage.print_usage_table(self.account, self.awarded, self.start_date)

            for call in mock_usage.call_args_list:
                args = call.args
                self.assertEqual(self.account, args[0])
                self.assertEqual(self.start_date, args[1])

    def test_usage_query_called_per_cluster(self) -> None:
        """get_cluster_usage_by_user is called once per cluster."""

        with mock.patch('apps.utils.system_info.Slurm.get_cluster_usage_by_user',
                        return_value=None) as mock_usage:
            with mock.patch('builtins.print'):
                CrcUsage.print_usage_table(self.account, self.awarded, self.start_date)

            self.assertEqual(len(self.awarded), mock_usage.call_count)

    def test_users_sorted_by_usage_descending(self) -> None:
        """Users with higher usage appear before users with lower usage."""

        output = self._capture_output_with_usage(
            {'user_low': 10, 'user_high': 900, 'total': 910}
        )
        high_pos = output.find('user_high')
        low_pos = output.find('user_low')
        self.assertLess(high_pos, low_pos)

    def test_small_percentage_shown_as_less_than_one(self) -> None:
        """Usage below 1% is displayed as '<1' rather than 0."""

        # print_usage_table calls .pop('total') on the returned dict, mutating
        # it in place. A side_effect lambda returns a fresh copy on every call
        # so the second cluster iteration does not hit a KeyError.
        # 1 / 1000 = 0.1% -- rounds to 0 by floor, should display '<1'
        with mock.patch('apps.utils.system_info.Slurm.get_cluster_usage_by_user',
                        side_effect=lambda *a, **kw: {'user1': 1, 'total': 1}):
            with mock.patch('builtins.print') as mock_print:
                CrcUsage.print_usage_table(self.account, self.awarded, self.start_date)
                output = '\n'.join(str(c.args[0]) for c in mock_print.call_args_list)

        self.assertIn('<1', output)


# ---------------------------------------------------------------------------
# Integration: missing Slurm account  (skipped if Slurm not installed)
# ---------------------------------------------------------------------------

@skipIf(not Slurm.is_installed(), 'Slurm is required to run this test')
class MissingAccountError(TestCase):
    """Test error handling when an account does not exist."""

    def test_error_on_fake_account(self) -> None:
        app = CrcUsage()
        args = app.parse_args(['dummy_account'])

        with self.assertRaisesRegex(RuntimeError, "No Slurm account was found with the name 'dummy_account'."):
            app.app_logic(args)