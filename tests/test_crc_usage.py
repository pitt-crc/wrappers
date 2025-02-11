"""Tests for the ``CrcUsage`` class."""

import grp
import os
from datetime import date
from unittest import TestCase, skipIf, mock

from apps.crc_usage import CrcUsage
from apps.utils.system_info import Slurm


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments"""

    def test_default_account(self) -> None:
        """Test the default account matches the current user's primary group"""

        parsed_account = CrcUsage().parse_args([]).account
        current_account = grp.getgrgid(os.getgid()).gr_name
        self.assertEqual(current_account, parsed_account)

    def test_custom_account_name(self) -> None:
        """Test a custom account is used when specified"""

        parsed_account = CrcUsage().parse_args(['dummy_account']).account
        self.assertEqual('dummy_account', parsed_account)


@skipIf(not Slurm.is_installed(), 'Slurm is required to run this test')
class MissingAccountError(TestCase):
    """Test error handling when an account does not exist"""

    def test_error_on_fake_account(self) -> None:
        """Test a ``RuntimeError`` is raised for a missing slurm account"""

        app = CrcUsage()
        args = app.parse_args(['dummy_account'])

        with self.assertRaisesRegex(RuntimeError, f"No Slurm account was found with the name 'dummy_account'."):
            app.app_logic(args)


class PrintSummaryTable(TestCase):
    """Test the `print_summary_table` method"""

    def setUp(self) -> None:
        """Set up the test environment with mock Slurm data"""

        self.account_name = 'test_account'
        self.alloc_requests = [
            {'id': 1, 'title': 'Request 1', 'expire': '2023-12-31'},
            {'id': 2, 'title': 'Request 2', 'expire': '2024-12-31'}
        ]
        self.per_request_totals = {
            1: {'cluster1': 1000, 'cluster2': 2000},
            2: {'cluster1': 1500, 'cluster2': 2500}
        }

    def test_summary_table_printed(self) -> None:
        """Test the summary table is created and printed"""

        with mock.patch('builtins.print') as mock_print:
            CrcUsage.print_summary_table(self.alloc_requests, self.account_name, self.per_request_totals)

            self.assertTrue(mock_print.called)

    def test_summary_table_values(self) -> None:
        """Test the summary table contains the correct headers"""

        with mock.patch('builtins.print') as mock_print:
            CrcUsage.print_summary_table(self.alloc_requests, self.account_name, self.per_request_totals)

            # Capture the printed output
            printed_output = "\n".join([str(call[0][0]) for call in mock_print.call_args_list])

            # Verify the table headers
            self.assertIn("Resource Allocation Request Information for 'test_account'", printed_output)
            self.assertIn("ID", printed_output)
            self.assertIn("TITLE", printed_output)
            self.assertIn("EXPIRATION DATE", printed_output)
            self.assertIn("CLUSTER", printed_output)
            self.assertIn("SERVICE UNITS", printed_output)

            # Verify specific rows
            self.assertIn("1", printed_output) # ID
            self.assertIn("Request 1", printed_output) # Title
            self.assertIn("2023-12-31", printed_output) # Expiration Date
            self.assertIn("cluster1", printed_output) # Cluster
            self.assertIn("1000", printed_output) # Service units

            self.assertIn("2", printed_output) # ID
            self.assertIn("Request 2", printed_output) # Title
            self.assertIn("2024-12-31", printed_output)  # Expiration Date
            self.assertIn("cluster2", printed_output) # Cluster
            self.assertIn("2500", printed_output) # Service Units


class PrintUsageTable(TestCase):
    """Test the `print_usage_table` method"""

    def setUp(self) -> None:
        """Set up the test environment with mock Slurm data"""

        self.account_name = 'test_account'
        self.awarded_totals = {'cluster1': 1000, 'cluster2': 2000}
        self.earliest_date = date(2023, 1, 1)

    @mock.patch('apps.utils.system_info.Slurm.get_cluster_usage_by_user')
    def test_usage_table_printed(self, mock_get_usage) -> None:
        """Test the creation and formatting of the usage table"""

        mock_get_usage.side_effect = lambda *args, **kwargs: {
            'user1': 100,
            'user2': 200,
            'total': 300
        }

        with mock.patch('builtins.print') as mock_print:
            CrcUsage.print_usage_table(self.account_name, self.awarded_totals, self.earliest_date)

            self.assertTrue(mock_print.called)

            # Capture the printed output
            printed_output = "\n".join([str(call[0][0]) for call in mock_print.call_args_list])

            # Verify the table contains the expected data
            # User 1 on Cluster 1
            self.assertIn("TOTAL USED: 300", printed_output) # Total Used
            self.assertIn("AWARDED: 1000", printed_output) # Total Awarded
            self.assertIn("% USED: 30", printed_output) # Total % Used
            self.assertIn("user1", printed_output) # User
            self.assertIn("100", printed_output) # Used
            self.assertIn("10", printed_output)  # % Used

            # User 2 on Cluster 2
            self.assertIn("TOTAL USED: 300", printed_output)  # Total Used
            self.assertIn("AWARDED: 2000", printed_output)  # Total Awarded
            self.assertIn("% USED: 15", printed_output)  # Total % Used
            self.assertIn("user2", printed_output)  # User
            self.assertIn("200", printed_output)  # Used
            self.assertIn("10", printed_output)  # % Used

    @mock.patch('apps.utils.system_info.Slurm.get_cluster_usage_by_user')
    def test_print_usage_table_no_data(self, mock_get_usage) -> None:
        """Test the usage table when no usage data is available"""

        # Mock no usage data
        mock_get_usage.return_value = None

        # Mock the print function to capture output
        with mock.patch('builtins.print') as mock_print:
            CrcUsage.print_usage_table(self.account_name, self.awarded_totals, self.earliest_date)

            # Verify the table was printed
            self.assertTrue(mock_print.called)

            # Capture the printed output
            printed_output = "\n".join([str(call[0][0]) for call in mock_print.call_args_list])

            # Verify the table contains the expected message for no data
            self.assertIn("TOTAL USED: 0", printed_output)
            self.assertIn("AWARDED: 1000", printed_output)
            self.assertIn("% USED: 0", printed_output)
