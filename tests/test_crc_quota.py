"""Tests for the ``crc-quota`` application."""

import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from apps.crc_quota import (AbstractFilesystemUsage, CrcQuota, GenericUsage, IhomeUsage, NO_QUOTA_MSG, VastUsage)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_statvfs(blocks: int = 1000, bavail: int = 200, frsize: int = 4096) -> MagicMock:
    """Return a mock statvfs result with predictable values.

    size_limit = blocks * frsize
    size_used  = (blocks - bavail) * frsize
    """

    stat = MagicMock()
    stat.f_blocks = blocks
    stat.f_bavail = bavail
    stat.f_frsize = frsize
    return stat


# ---------------------------------------------------------------------------
# AbstractFilesystemUsage.convert_size
# ---------------------------------------------------------------------------

class ConvertSize(TestCase):
    """Test byte-to-human-readable conversion."""

    def test_zero_bytes(self) -> None:
        self.assertEqual('0.0 B', AbstractFilesystemUsage.convert_size(0))

    def test_exact_power_of_two_units(self) -> None:
        cases = (
            (1, '1.0 B'),
            (2 ** 10, '1.0 KB'),
            (2 ** 20, '1.0 MB'),
            (2 ** 30, '1.0 GB'),
            (2 ** 40, '1.0 TB'),
            (2 ** 50, '1.0 PB'),
            (2 ** 60, '1.0 EB'),
            (2 ** 70, '1.0 ZB'),
            (2 ** 80, '1.0 YB'),
        )
        for size, expected in cases:
            with self.subTest(size=size):
                self.assertEqual(expected, AbstractFilesystemUsage.convert_size(size))

    def test_non_integer_values(self) -> None:
        cases = (
            (5, '5.0 B'),
            (5.0e5, '488.28 KB'),
            (5.0e7, '47.68 MB'),
            (5.0e9, '4.66 GB'),
            (5.0e12, '4.55 TB'),
        )
        for size, expected in cases:
            with self.subTest(size=size):
                self.assertEqual(expected, AbstractFilesystemUsage.convert_size(size))


# ---------------------------------------------------------------------------
# AbstractFilesystemUsage.to_string
# ---------------------------------------------------------------------------

class ToString(TestCase):
    """Test the short and verbose string representations."""

    def setUp(self) -> None:
        # 1 GB used, 2 GB limit
        self.quota = AbstractFilesystemUsage('zfs1', 2 ** 30, 2 ** 31)

    def test_short_string_format(self) -> None:
        """Short format: '-> name: used / limit'."""

        result = self.quota.to_string(verbose=False)
        self.assertEqual('-> zfs1: 1.0 GB / 2.0 GB', result)

    def test_verbose_string_format(self) -> None:
        """Verbose format: '-> name: Bytes Used: X, Byte Limit: Y'."""

        result = self.quota.to_string(verbose=True)
        self.assertEqual('-> zfs1: Bytes Used: 1.0 GB, Byte Limit: 2.0 GB', result)

    def test_default_is_short(self) -> None:
        """to_string() with no argument uses the short format."""

        self.assertEqual(self.quota.to_string(), self.quota.to_string(verbose=False))


# ---------------------------------------------------------------------------
# GenericUsage.from_path
# ---------------------------------------------------------------------------

class GenericUsageFromPath(TestCase):
    """Test GenericUsage construction from a filesystem path."""

    @patch('os.statvfs')
    def test_returns_instance_for_valid_path(self, mock_statvfs) -> None:
        """A GenericUsage instance is returned when statvfs succeeds."""

        mock_statvfs.return_value = _mock_statvfs(blocks=1000, bavail=200, frsize=4096)
        result = GenericUsage.from_path('zfs1', '/zfs1/mygroup')

        self.assertIsInstance(result, GenericUsage)
        self.assertEqual('zfs1', result.name)

    @patch('os.statvfs')
    def test_size_calculations_correct(self, mock_statvfs) -> None:
        """size_used and size_limit are calculated from statvfs fields."""

        mock_statvfs.return_value = _mock_statvfs(blocks=1000, bavail=200, frsize=4096)
        result = GenericUsage.from_path('zfs1', '/zfs1/mygroup')

        self.assertEqual(1000 * 4096, result.size_limit)
        self.assertEqual((1000 - 200) * 4096, result.size_used)

    @patch('os.statvfs', side_effect=FileNotFoundError)
    def test_returns_none_for_missing_path(self, _) -> None:
        """None is returned when the path does not exist."""

        self.assertIsNone(GenericUsage.from_path('zfs1', '/zfs1/nonexistent'))

    @patch('os.statvfs', side_effect=OSError)
    def test_returns_none_on_os_error(self, _) -> None:
        """None is returned on a general OS error."""

        self.assertIsNone(GenericUsage.from_path('zfs1', '/zfs1/mygroup'))


# ---------------------------------------------------------------------------
# IhomeUsage
# ---------------------------------------------------------------------------

class IhomeUsageStrings(TestCase):
    """Test IhomeUsage string representations."""

    def test_short_string_with_quota(self) -> None:
        quota = IhomeUsage('ihome', 2 ** 30, 2 ** 31, has_quota=True)
        self.assertEqual('-> ihome: 1.0 GB / 2.0 GB', quota.to_string())

    def test_short_string_without_quota(self) -> None:
        quota = IhomeUsage('ihome', 2 ** 30, 2 ** 31, has_quota=False)
        result = quota.to_string()
        self.assertIn(NO_QUOTA_MSG, result)
        self.assertNotIn('2.0 GB', result)

    def test_verbose_string_with_quota(self) -> None:
        quota = IhomeUsage('ihome', 2 ** 30, 2 ** 31, has_quota=True)
        result = quota.to_string(verbose=True)
        self.assertIn('Bytes Used:', result)
        self.assertIn('Byte Limit:', result)

    def test_verbose_string_without_quota(self) -> None:
        quota = IhomeUsage('ihome', 2 ** 30, 2 ** 31, has_quota=False)
        result = quota.to_string(verbose=True)
        self.assertIn(NO_QUOTA_MSG, result)
        self.assertNotIn('Byte Limit:', result)


class IhomeUsageFromPath(TestCase):
    """Test IhomeUsage.from_path quota detection heuristic."""

    def _patch_statvfs(self, user_blocks, user_frsize, mount_blocks, mount_frsize):
        """Patch os.statvfs to return different results for user path vs /ihome."""

        user_stat = _mock_statvfs(blocks=user_blocks, bavail=0, frsize=user_frsize)
        mount_stat = _mock_statvfs(blocks=mount_blocks, bavail=0, frsize=mount_frsize)

        def side_effect(path):
            if path == '/ihome':
                return mount_stat
            return user_stat

        return patch('os.statvfs', side_effect=side_effect)

    def test_quota_detected_when_size_differs_from_mount(self) -> None:
        """has_quota=True when user directory is much smaller than the mount."""

        # User dir: 5 GB, mount: 100 GB — clearly a quota is set
        with self._patch_statvfs(user_blocks=1280, user_frsize=4096,
            mount_blocks=25600, mount_frsize=4096):
            result = IhomeUsage.from_path('ihome', '/ihome/user1')

        self.assertIsNotNone(result)
        self.assertTrue(result.has_quota)

    def test_no_quota_when_size_matches_mount(self) -> None:
        """has_quota=False when user directory size is within 1% of the mount."""

        # Same blocks and frsize — ratio is exactly 1.0
        with self._patch_statvfs(user_blocks=25600, user_frsize=4096,
            mount_blocks=25600, mount_frsize=4096):
            result = IhomeUsage.from_path('ihome', '/ihome/user1')

        self.assertIsNotNone(result)
        self.assertFalse(result.has_quota)

    def test_returns_none_for_missing_path(self) -> None:
        with patch('os.statvfs', side_effect=FileNotFoundError):
            self.assertIsNone(IhomeUsage.from_path('ihome', '/ihome/nobody'))

    def test_no_quota_when_mount_size_is_zero(self) -> None:
        """has_quota=False when mount reports zero blocks (edge case)."""

        user_stat = _mock_statvfs(blocks=100, bavail=0, frsize=4096)
        mount_stat = _mock_statvfs(blocks=0, bavail=0, frsize=4096)

        def side_effect(path):
            return mount_stat if path == '/ihome' else user_stat

        with patch('os.statvfs', side_effect=side_effect):
            result = IhomeUsage.from_path('ihome', '/ihome/user1')

        self.assertFalse(result.has_quota)


# ---------------------------------------------------------------------------
# VastUsage
# ---------------------------------------------------------------------------

class VastUsageStrings(TestCase):
    """Test VastUsage string representations."""

    def test_short_string_with_quota(self) -> None:
        quota = VastUsage('vast', 2 ** 30, 2 ** 31, has_quota=True)
        self.assertEqual('-> vast: 1.0 GB / 2.0 GB', quota.to_string())

    def test_short_string_without_quota(self) -> None:
        quota = VastUsage('vast', 2 ** 30, 2 ** 31, has_quota=False)
        self.assertIn(NO_QUOTA_MSG, quota.to_string())

    def test_verbose_string_with_quota(self) -> None:
        quota = VastUsage('vast', 2 ** 30, 2 ** 31, has_quota=True)
        result = quota.to_string(verbose=True)
        self.assertIn('Bytes Used:', result)
        self.assertIn('Byte Limit:', result)

    def test_verbose_string_without_quota(self) -> None:
        quota = VastUsage('vast', 2 ** 30, 2 ** 31, has_quota=False)
        result = quota.to_string(verbose=True)
        self.assertIn(NO_QUOTA_MSG, result)


class VastUsageFromPath(TestCase):
    """Test VastUsage.from_path quota detection heuristic."""

    def _patch_statvfs(self, user_blocks, user_frsize, mount_blocks, mount_frsize):
        user_stat = _mock_statvfs(blocks=user_blocks, bavail=0, frsize=user_frsize)
        mount_stat = _mock_statvfs(blocks=mount_blocks, bavail=0, frsize=mount_frsize)

        def side_effect(path):
            if path == '/vast':
                return mount_stat
            return user_stat

        return patch('os.statvfs', side_effect=side_effect)

    def test_quota_detected_when_size_differs_from_mount(self) -> None:
        with self._patch_statvfs(user_blocks=1280, user_frsize=4096,
            mount_blocks=25600, mount_frsize=4096):
            result = VastUsage.from_path('vast', '/vast/mygroup')

        self.assertIsNotNone(result)
        self.assertTrue(result.has_quota)

    def test_no_quota_when_size_matches_mount(self) -> None:
        with self._patch_statvfs(user_blocks=25600, user_frsize=4096,
            mount_blocks=25600, mount_frsize=4096):
            result = VastUsage.from_path('vast', '/vast/mygroup')

        self.assertIsNotNone(result)
        self.assertFalse(result.has_quota)

    def test_returns_none_for_missing_path(self) -> None:
        with patch('os.statvfs', side_effect=FileNotFoundError):
            self.assertIsNone(VastUsage.from_path('vast', '/vast/nobody'))


# ---------------------------------------------------------------------------
# CrcQuota — argument parsing
# ---------------------------------------------------------------------------

class ArgumentParsing(TestCase):
    """Test the parsing of command line arguments."""

    def test_user_defaults_to_none(self) -> None:
        """User argument defaults to None (current user will be looked up)."""

        args, _ = CrcQuota().parse_known_args([])
        self.assertIsNone(args.user)

    def test_explicit_user_stored(self) -> None:
        """An explicit username is stored on the parsed args."""

        args, _ = CrcQuota().parse_known_args(['user1'])
        self.assertEqual('user1', args.user)

    def test_verbose_defaults_to_false(self) -> None:
        args, _ = CrcQuota().parse_known_args([])
        self.assertFalse(args.verbose)

    def test_verbose_flag_sets_true(self) -> None:
        args, _ = CrcQuota().parse_known_args(['--verbose'])
        self.assertTrue(args.verbose)


# ---------------------------------------------------------------------------
# CrcQuota.get_user_info
# ---------------------------------------------------------------------------

class GetUserInfo(TestCase):
    """Test get_user_info returns correct system identity fields."""

    def test_returns_current_user_when_no_username_given(self) -> None:
        """Returns current user's info when username is None."""

        user, uid, group, gid, homedir = CrcQuota.get_user_info(None)
        self.assertIsInstance(user, str)
        self.assertIsInstance(uid, int)
        self.assertIsInstance(group, str)
        self.assertIsInstance(gid, int)
        self.assertIsInstance(homedir, str)
        self.assertEqual(os.getuid(), uid)

    def test_exits_for_unknown_user(self) -> None:
        """sys.exit is called when the username does not exist."""

        with self.assertRaises(SystemExit):
            CrcQuota.get_user_info('this_user_definitely_does_not_exist_xyzzy')


# ---------------------------------------------------------------------------
# CrcQuota.get_group_quotas
# ---------------------------------------------------------------------------

class GetGroupQuotas(TestCase):
    """Test get_group_quotas returns only quotas for paths that exist."""

    @patch('os.statvfs', side_effect=FileNotFoundError)
    def test_returns_empty_tuple_when_no_paths_exist(self, _) -> None:
        """Empty tuple returned when none of the group paths exist."""

        result = CrcQuota.get_group_quotas('nonexistent_group')
        self.assertEqual((), result)

    def test_returns_only_non_none_quotas(self) -> None:
        """Only paths that exist are included in the returned tuple."""

        real_stat = _mock_statvfs()

        def statvfs_side_effect(path):
            # Only /zfs1/mygroup "exists"
            if '/zfs1/' in path:
                return real_stat
            raise FileNotFoundError

        with patch('os.statvfs', side_effect=statvfs_side_effect):
            result = CrcQuota.get_group_quotas('mygroup')

        self.assertEqual(1, len(result))
        self.assertEqual('zfs1', result[0].name)

