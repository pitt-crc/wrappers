"""Tests for the ``crc-interactive`` application."""

from argparse import ArgumentTypeError, Namespace
from datetime import time
from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch

from apps.crc_interactive import CrcInteractive


# ---------------------------------------------------------------------------
# Helpers — build a fully-populated Namespace so individual tests can
# override only the fields they care about without repeating boilerplate.
# ---------------------------------------------------------------------------

def _default_args(**overrides) -> Namespace:
    """Return a Namespace with sensible defaults for create_srun_command tests."""

    base = dict(
        print_command=False,
        smp=False, gpu=False, mpi=False, invest=False, htc=False, teach=False,
        partition=None,
        mem=CrcInteractive.default_mem,
        time=CrcInteractive.default_time,
        num_nodes=CrcInteractive.default_nodes,
        num_cores=CrcInteractive.default_cores,
        num_gpus=CrcInteractive.default_gpus,
        account=None,
        reservation=None,
        license=None,
        feature=None,
        openmp=False,
    )
    base.update(overrides)
    return Namespace(**base)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments."""

    def setUp(self) -> None:
        self.app = CrcInteractive()

    def test_defaults_match_class_settings(self) -> None:
        """Parsed defaults match the class-level default constants."""

        args = self.app.parse_args(['--smp'])
        self.assertEqual(CrcInteractive.default_time, args.time)
        self.assertEqual(CrcInteractive.default_cores, args.num_cores)
        self.assertEqual(CrcInteractive.default_mem, args.mem)
        self.assertEqual(CrcInteractive.default_gpus, args.num_gpus)
        self.assertEqual(CrcInteractive.default_nodes, args.num_nodes)

    def test_gpu_default_is_zero_on_non_gpu_cluster(self) -> None:
        """GPU count defaults to 0 on non-GPU clusters."""

        args = self.app.parse_args(['--smp'])
        self.assertEqual(0, args.num_gpus)

    def test_gpu_default_is_one_on_gpu_cluster(self) -> None:
        """GPU count defaults to 1 when the gpu cluster is selected."""

        args = self.app.parse_args(['--gpu'])
        self.assertEqual(1, args.num_gpus)

    def test_explicit_gpu_count_respected(self) -> None:
        """An explicit --num-gpus value overrides the dynamic default."""

        args = self.app.parse_args(['--gpu', '--num-gpus', '4'])
        self.assertEqual(4, args.num_gpus)

    def test_time_too_short_raises_error(self) -> None:
        """Times below the minimum raise a SystemExit."""

        with self.assertRaisesRegex(SystemExit, 'Requested time must be'):
            self.app.parse_args(['--smp', '--time', '00:00:30'])

    def test_time_too_long_raises_error(self) -> None:
        """Times above the maximum raise a SystemExit."""

        with self.assertRaisesRegex(SystemExit, 'Requested time must be'):
            self.app.parse_args(['--smp', '--time', '00:50:00'])

    def test_time_at_minimum_boundary_accepted(self) -> None:
        """The exact minimum time is accepted without error."""

        args = self.app.parse_args(['--smp', '--time', str(CrcInteractive.min_time)])
        self.assertEqual(CrcInteractive.min_time, args.time.hour)

    def test_time_at_maximum_boundary_accepted(self) -> None:
        """The exact maximum time is accepted without error."""

        args = self.app.parse_args(['--smp', '--time', str(CrcInteractive.max_time)])
        self.assertEqual(CrcInteractive.max_time, args.time.hour)

    def test_mpi_minimum_nodes_enforced(self) -> None:
        """Fewer than the minimum MPI nodes raises a SystemExit."""

        min_nodes = CrcInteractive.min_mpi_nodes
        min_cores = CrcInteractive.min_mpi_cores.default_factory()

        with self.assertRaisesRegex(SystemExit, 'You must use at least .* nodes'):
            self.app.parse_args(['--mpi', '--num-nodes', str(min_nodes - 1), '--num-cores', str(min_cores)])

    def test_mpi_minimum_cores_enforced(self) -> None:
        """Fewer than the minimum MPI cores raises a SystemExit."""

        min_nodes = CrcInteractive.min_mpi_nodes
        min_cores = CrcInteractive.min_mpi_cores.default_factory()

        with self.assertRaisesRegex(SystemExit, 'You must request at least .* cores'):
            self.app.parse_args(['--mpi', '--num-nodes', str(min_nodes), '--num-cores', str(min_cores - 1)])

    def test_mpi_at_minimum_values_accepted(self) -> None:
        """Exactly the minimum MPI nodes and cores are accepted."""

        min_nodes = CrcInteractive.min_mpi_nodes
        min_cores = CrcInteractive.min_mpi_cores.default_factory()
        self.app.parse_args(['--mpi', '--num-nodes', str(min_nodes), '--num-cores', str(min_cores)])

    def test_mpi_partition_specific_minimum_cores(self) -> None:
        """opa-high-mem partition enforces its own minimum core count."""

        min_nodes = CrcInteractive.min_mpi_nodes
        opa_min = CrcInteractive.min_mpi_cores['opa-high-mem']

        with self.assertRaisesRegex(SystemExit, 'You must request at least .* cores'):
            self.app.parse_args([
                '--mpi', '--partition', 'opa-high-mem',
                '--num-nodes', str(min_nodes),
                '--num-cores', str(opa_min - 1),
            ])

    def test_invest_requires_partition(self) -> None:
        """Using --invest without --partition raises a SystemExit."""

        with self.assertRaisesRegex(SystemExit, 'You must specify a partition'):
            self.app.parse_args(['--invest'])

    def test_invest_with_partition_accepted(self) -> None:
        """Using --invest with --partition is accepted."""

        args = self.app.parse_args(['--invest', '--partition', 'my-partition'])
        self.assertTrue(args.invest)
        self.assertEqual('my-partition', args.partition)

    def test_optional_flags_stored(self) -> None:
        """Optional flags (account, reservation, license, feature) are stored."""

        args = self.app.parse_args([
            '--smp',
            '--account', 'myaccount',
            '--reservation', 'myreservation',
            '--license', 'myapp',
            '--feature', 'ti',
        ])
        self.assertEqual('myaccount', args.account)
        self.assertEqual('myreservation', args.reservation)
        self.assertEqual('myapp', args.license)
        self.assertEqual('ti', args.feature)

    def test_openmp_flag_stored(self) -> None:
        """The --openmp flag is stored as True."""

        args = self.app.parse_args(['--smp', '--openmp'])
        self.assertTrue(args.openmp)


# ---------------------------------------------------------------------------
# Time parsing
# ---------------------------------------------------------------------------

class ParseTime(TestCase):
    """Test the static ``parse_time`` method."""

    def test_integer_hour(self) -> None:
        """A bare integer is interpreted as hours."""

        self.assertEqual(time(1, 0, 0), CrcInteractive.parse_time('1'))
        self.assertEqual(time(1, 0, 0), CrcInteractive.parse_time('01'))

    def test_hours_and_minutes(self) -> None:
        """HH:MM format is parsed correctly."""

        self.assertEqual(time(23, 59, 0), CrcInteractive.parse_time('23:59'))

    def test_hours_minutes_seconds(self) -> None:
        """HH:MM:SS format is parsed correctly."""

        self.assertEqual(time(12, 34, 56), CrcInteractive.parse_time('12:34:56'))

    def test_wrong_delimiter_raises(self) -> None:
        """Hyphens instead of colons raise ArgumentTypeError."""

        with self.assertRaises(ArgumentTypeError):
            CrcInteractive.parse_time('12-34-56')

    def test_too_many_segments_raises(self) -> None:
        """More than three colon-separated segments raise ArgumentTypeError."""

        with self.assertRaises(ArgumentTypeError):
            CrcInteractive.parse_time('12:34:56:78')

    def test_out_of_range_hour_raises(self) -> None:
        with self.assertRaises(ArgumentTypeError):
            CrcInteractive.parse_time('25:00:00')

    def test_out_of_range_minute_raises(self) -> None:
        with self.assertRaises(ArgumentTypeError):
            CrcInteractive.parse_time('12:60:00')

    def test_out_of_range_second_raises(self) -> None:
        with self.assertRaises(ArgumentTypeError):
            CrcInteractive.parse_time('12:34:60')

    def test_empty_string_raises(self) -> None:
        with self.assertRaises(ArgumentTypeError):
            CrcInteractive.parse_time('')

    def test_non_numeric_raises(self) -> None:
        with self.assertRaises(ArgumentTypeError):
            CrcInteractive.parse_time('ab:cd')


# ---------------------------------------------------------------------------
# srun command construction
# ---------------------------------------------------------------------------

class CreateSrunCommand(TestCase):
    """Test the srun command string built by ``create_srun_command``."""

    def setUp(self) -> None:
        self.app = CrcInteractive()

    # --- cluster flag ---

    def test_cluster_flag_in_command(self) -> None:
        """The selected cluster name appears after -M."""

        cmd = self.app.create_srun_command(_default_args(smp=True))
        self.assertIn('-M smp', cmd)

    def test_gpu_cluster_flag(self) -> None:
        cmd = self.app.create_srun_command(_default_args(gpu=True, num_gpus=1))
        self.assertIn('-M gpu', cmd)

    def test_mpi_cluster_flag(self) -> None:
        cmd = self.app.create_srun_command(
            _default_args(mpi=True, partition='mpi',
                num_nodes=CrcInteractive.min_mpi_nodes,
                num_cores=CrcInteractive.min_mpi_cores.default_factory()))
        self.assertIn('-M mpi', cmd)

    def test_no_cluster_raises_runtime_error(self) -> None:
        """RuntimeError is raised when no cluster flag is set."""

        with self.assertRaises(RuntimeError):
            self.app.create_srun_command(_default_args())

    # --- resource flags ---

    def test_nodes_flag(self) -> None:
        cmd = self.app.create_srun_command(_default_args(smp=True, num_nodes=3))
        self.assertIn('--nodes=3', cmd)

    def test_mem_flag(self) -> None:
        cmd = self.app.create_srun_command(_default_args(smp=True, mem=8))
        self.assertIn('--mem=8g', cmd)

    def test_time_flag(self) -> None:
        cmd = self.app.create_srun_command(_default_args(smp=True, time=time(2, 30)))
        self.assertIn('--time=02:30:00', cmd)

    def test_ntasks_per_node_without_openmp(self) -> None:
        """Without --openmp, cores are passed as --ntasks-per-node."""

        cmd = self.app.create_srun_command(_default_args(smp=True, num_cores=8, openmp=False))
        self.assertIn('--ntasks-per-node=8', cmd)
        self.assertNotIn('--cpus-per-task', cmd)

    def test_cpus_per_task_with_openmp(self) -> None:
        """With --openmp, cores are passed as --cpus-per-task."""

        cmd = self.app.create_srun_command(_default_args(smp=True, num_cores=8, openmp=True))
        self.assertIn('--cpus-per-task=8', cmd)
        self.assertNotIn('--ntasks-per-node', cmd)

    def test_gpu_gres_flag(self) -> None:
        """GPU count is passed as --gres=gpu:N for the gpu cluster."""

        cmd = self.app.create_srun_command(_default_args(gpu=True, num_gpus=2))
        self.assertIn('--gres=gpu:2', cmd)

    def test_no_gres_on_cpu_cluster(self) -> None:
        """--gres is not added for CPU-only clusters."""

        cmd = self.app.create_srun_command(_default_args(smp=True, num_gpus=0))
        self.assertNotIn('--gres', cmd)

    def test_partition_flag(self) -> None:
        cmd = self.app.create_srun_command(_default_args(mpi=True, partition='opa-high-mem',
            num_nodes=2, num_cores=28))
        self.assertIn('--partition=opa-high-mem', cmd)

    # --- optional flags ---

    def test_account_flag(self) -> None:
        cmd = self.app.create_srun_command(_default_args(smp=True, account='myaccount'))
        self.assertIn('--account=myaccount', cmd)

    def test_reservation_flag(self) -> None:
        cmd = self.app.create_srun_command(_default_args(smp=True, reservation='myreserv'))
        self.assertIn('--reservation=myreserv', cmd)

    def test_license_flag(self) -> None:
        cmd = self.app.create_srun_command(_default_args(smp=True, license='matlab'))
        self.assertIn('--licenses=matlab', cmd)

    def test_feature_flag(self) -> None:
        cmd = self.app.create_srun_command(_default_args(smp=True, feature='ti'))
        self.assertIn('--constraint=ti', cmd)

    def test_export_all_always_present(self) -> None:
        """--export=ALL is always included in the srun command."""

        cmd = self.app.create_srun_command(_default_args(smp=True))
        self.assertIn('--export=ALL', cmd)

    def test_pty_bash_always_present(self) -> None:
        """Command always ends with --pty bash."""

        cmd = self.app.create_srun_command(_default_args(smp=True))
        self.assertTrue(cmd.endswith('--pty bash'))

    # --- full command regression tests ---

    def test_full_gpu_command(self) -> None:
        """Full srun command for the gpu cluster matches expected string."""

        args = _default_args(gpu=True, mem=2, time=time(2, 0), num_nodes=2,
            num_cores=4, num_gpus=1)
        expected = (
            'srun -M gpu --export=ALL '
            '--nodes=2 --time=02:00:00 --mem=2g --ntasks-per-node=4 --gres=gpu:1 --pty bash'
        )
        self.assertEqual(expected, self.app.create_srun_command(args))

    def test_full_mpi_command(self) -> None:
        """Full srun command for the mpi cluster matches expected string."""

        args = _default_args(mpi=True, partition='mpi', mem=4, time=time(3, 0),
            num_nodes=3, num_cores=48)
        expected = (
            'srun -M mpi --export=ALL --partition=mpi '
            '--nodes=3 --time=03:00:00 --mem=4g --ntasks-per-node=48 --pty bash'
        )
        self.assertEqual(expected, self.app.create_srun_command(args))

    def test_full_invest_command(self) -> None:
        """Full srun command for the invest cluster matches expected string."""

        args = _default_args(invest=True, partition='invest-partition',
            mem=2, time=time(1, 0), num_nodes=1, num_cores=4)
        expected = (
            'srun -M invest --export=ALL --partition=invest-partition '
            '--nodes=1 --time=01:00:00 --mem=2g --ntasks-per-node=4 --pty bash'
        )
        self.assertEqual(expected, self.app.create_srun_command(args))


# ---------------------------------------------------------------------------
# app_logic — print vs execute
# ---------------------------------------------------------------------------

class AppLogic(TestCase):
    """Test that app_logic prints the command or executes it appropriately."""

    # app_logic calls Slurm.get_cluster_names() to check which cluster was
    # selected. That method tries to run squeue, which doesn't exist in the
    # test environment, so it must be mocked in every test here.
    _cluster_names = {'smp', 'gpu', 'mpi', 'invest', 'htc', 'teach'}

    @patch('apps.crc_interactive.Slurm.get_cluster_names')
    @patch('apps.crc_interactive.system')
    def test_executes_srun_by_default(self, mock_system: Mock, mock_clusters: Mock) -> None:
        """Without --print-command, the srun command is executed via os.system."""

        mock_clusters.return_value = self._cluster_names
        CrcInteractive().execute(['--smp'])
        mock_system.assert_called_once()
        cmd = mock_system.call_args.args[0]
        self.assertIn('srun', cmd)
        self.assertIn('-M smp', cmd)

    @patch('apps.crc_interactive.Slurm.get_cluster_names')
    @patch('sys.stdout', new_callable=StringIO)
    @patch('apps.crc_interactive.system')
    def test_print_command_flag_prints_and_does_not_execute(
        self, mock_system: Mock, mock_stdout: Mock, mock_clusters: Mock
    ) -> None:
        """With --print-command, the command is printed and os.system is not called."""

        mock_clusters.return_value = self._cluster_names
        CrcInteractive().execute(['--smp', '--print-command'])
        mock_system.assert_not_called()
        self.assertIn('srun', mock_stdout.getvalue())

    @patch('apps.crc_interactive.Slurm.get_cluster_names')
    def test_no_cluster_prints_help_and_exits(self, mock_clusters: Mock) -> None:
        """With no cluster flag, the app prints help and exits cleanly."""

        mock_clusters.return_value = self._cluster_names
        with self.assertRaises(SystemExit):
            CrcInteractive().execute([])
