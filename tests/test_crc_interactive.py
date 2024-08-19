"""Tests for the ``crc-interactive`` application."""

from argparse import ArgumentTypeError, Namespace
from datetime import time
from unittest import TestCase

from apps.crc_interactive import CrcInteractive


class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments."""

    def setUp(self) -> None:
        """Set up the test environment."""

        self.app = CrcInteractive()

    def test_args_match_class_settings(self) -> None:
        """Test parsed args default to the values defined as class settings."""

        args = self.app.parse_args(['--smp'])

        self.assertEqual(CrcInteractive.default_time, args.time)
        self.assertEqual(CrcInteractive.default_cores, args.num_cores)
        self.assertEqual(CrcInteractive.default_mem, args.mem)
        self.assertEqual(CrcInteractive.default_gpus, args.num_gpus)

    def test_time_argument_out_of_range(self) -> None:
        """Test invalid time arguments raise an error."""

        # Time too short
        with self.assertRaisesRegex(SystemExit, 'Requested time must be', msg='Minimum MPI time not enforced.'):
            self.app.parse_args(['--smp', '--time', '00:00:30'])

        # Time too long
        with self.assertRaisesRegex(SystemExit, 'Requested time must be', msg='Maximum MPI time not enforced.'):
            self.app.parse_args(['--smp', '--time', '00:50:00'])

    def test_mpi_minimums(self) -> None:
        """Test minimum usage limits on MPI."""

        min_nodes = CrcInteractive.min_mpi_nodes
        min_cores = CrcInteractive.min_mpi_cores.default_factory()

        # Minimum values should parse without any errors
        self.app.parse_args(['--mpi', '--num-nodes', str(min_nodes), '--num-cores', str(min_cores)])

        nodes_err_message = 'You must use at least .* nodes'
        with self.assertRaisesRegex(SystemExit, nodes_err_message, msg='Minimum nodes not enforced.'):
            self.app.parse_args(['--mpi', '--num-nodes', str(min_nodes - 1), '--num-cores', str(min_cores)])

        cores_error_message = 'You must request at least .* cores'
        with self.assertRaisesRegex(SystemExit, cores_error_message, msg='Minimum cores not enforced.'):
            self.app.parse_args(['--mpi', '--num-nodes', str(min_nodes), '--num-cores', str(min_cores - 1)])

    def test_invest_partition_required(self) -> None:
        """Test a partition must be specified for the invest cluster."""

        with self.assertRaisesRegex(SystemExit, 'You must specify a partition'):
            self.app.parse_args(['--invest'])


class TestParseTime(TestCase):
    """Test the parsing of time strings."""

    def test_valid_time(self) -> None:
        """Test the parsing of valid time strings."""

        self.assertEqual(CrcInteractive.parse_time('1'), time(1, 0, 0))
        self.assertEqual(CrcInteractive.parse_time('01'), time(1, 0, 0))
        self.assertEqual(CrcInteractive.parse_time('23:59'), time(23, 59, 0))
        self.assertEqual(CrcInteractive.parse_time('12:34:56'), time(12, 34, 56))

    def test_invalid_time_format(self) -> None:
        """Test an errr is raised for invalid time formatting."""

        # Test with invalid time formats
        with self.assertRaises(ArgumentTypeError, msg='Error not raised for invalid delimiter'):
            CrcInteractive.parse_time('12-34-56')

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for too many digits'):
            CrcInteractive.parse_time('123:456:789')

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for too many segments'):
            CrcInteractive.parse_time('12:34:56:78')

    def test_invalid_time_value(self) -> None:
        """Test an errr is raised for invalid time values."""

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for invalid hour'):
            CrcInteractive.parse_time('25:00:00')

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for invalid minute'):
            CrcInteractive.parse_time('12:60:00')

        with self.assertRaises(ArgumentTypeError, msg='Error not raised for invalid second'):
            CrcInteractive.parse_time('12:34:60')

    def test_empty_string(self) -> None:
        """Test an error is raised for empty strings."""

        with self.assertRaises(ArgumentTypeError):
            CrcInteractive.parse_time('')


class CreateSrunCommand(TestCase):
    """Test the creation of `srun` commands."""

    def setUp(self) -> None:
        """Set up the test environment."""

        self.app = CrcInteractive()

    def test_gpu_cluster(self) -> None:
        """Test generating an `srun` command for the `gpu` cluster."""

        args = Namespace(
            print_command=False,
            smp=False,
            gpu=True,
            mpi=False,
            invest=False,
            htc=False,
            teach=False,
            partition=None,
            mem=2,
            time=time(2, 0),
            num_nodes=2,
            num_cores=4,
            num_gpus=1,
            account=None,
            reservation=None,
            license=None,
            feature=None,
            openmp=False
        )

        expected_command = 'srun -M gpu --export=ALL --nodes=2 --time=02:00:00 --mem=2g --ntasks-per-node=4 --gres=gpu:1 --pty bash'
        actual_command = self.app.create_srun_command(args)
        self.assertEqual(expected_command, actual_command)

    def test_mpi_cluster(self) -> None:
        """Test generating an `srun` command for the `gpu` cluster."""

        args = Namespace(
            print_command=False,
            smp=False,
            gpu=False,
            mpi=True,
            invest=False,
            htc=False,
            teach=False,
            partition='mpi',
            mem=4,
            time=time(3, 0),
            num_nodes=3,
            num_cores=48,
            num_gpus=0,
            account=None,
            reservation=None,
            license=None,
            feature=None,
            openmp=False
        )

        expected_command = 'srun -M mpi --export=ALL --partition=mpi --nodes=3 --time=03:00:00 --mem=4g --ntasks-per-node=48 --pty bash'
        actual_command = self.app.create_srun_command(args)
        self.assertEqual(expected_command, actual_command)

    def test_invest_command(self) -> None:
        """Test srun command for the invest cluster."""

        args = Namespace(
            print_command=False,
            smp=False,
            gpu=False,
            mpi=False,
            invest=True,
            htc=False,
            teach=False,
            partition='invest-partition',
            mem=2,
            time=time(1, 0),
            num_nodes=1,
            num_cores=4,
            num_gpus=0,
            account=None,
            reservation=None,
            license=None,
            feature=None,
            openmp=False
        )

        expected_command = 'srun -M invest --export=ALL --partition=invest-partition --nodes=1 --time=01:00:00 --mem=2g --ntasks-per-node=4 --pty bash'
        actual_command = self.app.create_srun_command(args)
        self.assertEqual(expected_command, actual_command)

    def test_partition_specific_cores(self) -> None:
        """Test srun command with partition-specific core requirements."""

        args = Namespace(
            print_command=False,
            smp=False,
            gpu=False,
            mpi=True,
            invest=False,
            htc=False,
            teach=False,
            partition='opa-high-mem',
            mem=8,
            time=time(2, 0),
            num_nodes=2,
            num_cores=28,
            num_gpus=0,
            account=None,
            reservation=None,
            license=None,
            feature=None,
            openmp=False
        )

        expected_command = 'srun -M mpi --export=ALL --partition=opa-high-mem --nodes=2 --time=02:00:00 --mem=8g --ntasks-per-node=28 --pty bash'
        actual_command = self.app.create_srun_command(args)
        self.assertEqual(expected_command, actual_command)

    def test_no_cluster_specified(self) -> None:
        """Test an error is raised when no cluster is specified."""

        args = Namespace(
            print_command=False,
            smp=False,
            gpu=False,
            mpi=False,
            invest=False,
            htc=False,
            teach=False,
            partition=None,
            mem=1,
            time=time(1, 0),
            num_nodes=1,
            num_cores=4,
            num_gpus=0,
            account=None,
            reservation=None,
            license=None,
            feature=None,
            openmp=True
        )

        with self.assertRaises(RuntimeError):
            self.app.create_srun_command(args)
