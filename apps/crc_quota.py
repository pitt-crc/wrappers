"""Command line application for reporting a user's disk quota usage.

The `crc-quota` application prints disk usage across multiple CRC file systems
for a given user. Quota limits are determined using `os.statvfs`. On VAST
file systems, the quota limit is reported as the file system size, so a
heuristic comparison against the mount point is used to detect whether a quota
is actually configured.
"""

from __future__ import annotations

import math
import os
import pwd
import sys
from argparse import Namespace

from .utils.cli import BaseParser

NO_QUOTA_MSG = 'No Quota Found, Please contact the CRCD Team to fix this!'


class AbstractFilesystemUsage:
    """Base class for representing disk quota usage on a single file system."""

    def __init__(self, name: str, size_used: int, size_limit: int) -> None:
        """Create a new quota object from known system metrics.

        Args:
            name: The name of the file system (e.g., zfs1, ihome).
            size_used: Bytes consumed by the user or group.
            size_limit: Maximum bytes allowed by the allocation.
        """

        self.name = name
        self.size_used = size_used
        self.size_limit = size_limit

    def to_string(self, verbose: bool = False) -> str:
        """Return a human-readable representation of the quota usage.

        Args:
            verbose: Whether to use the verbose format with labeled fields.

        Returns:
            A formatted string describing current usage and the quota limit.
        """

        if verbose:
            return self._verbose_string()

        return self._short_string()

    def _verbose_string(self) -> str:
        used = self.convert_size(self.size_used)
        limit = self.convert_size(self.size_limit)
        return f'-> {self.name}: Bytes Used: {used}, Byte Limit: {limit}'

    def _short_string(self) -> str:
        used = self.convert_size(self.size_used)
        limit = self.convert_size(self.size_limit)
        return f'-> {self.name}: {used} / {limit}'

    @staticmethod
    def convert_size(size: int) -> str:
        """Convert a byte count to a human-readable string with units.

        Args:
            size: A number of bytes.

        Returns:
            A string representation of the size with appropriate units.
        """

        if size == 0:
            return '0.0 B'

        base_2_power = int(math.floor(math.log(size, 1024)))
        conversion_factor = math.pow(1024, base_2_power)
        final_size = round(size / conversion_factor, 2)

        size_units = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
        return f'{final_size} {size_units[base_2_power]}'


class GenericUsage(AbstractFilesystemUsage):
    """Disk quota for a generic (non-VAST) file system."""

    @classmethod
    def from_path(cls, name: str, path: str) -> GenericUsage | None:
        """Return a quota object for the given file path.

        Args:
            name: The name of the file system.
            path: The file system path to measure.

        Returns:
            A `GenericUsage` instance, or None if the path does not exist.
        """

        try:
            stat = os.statvfs(path)
        except (OSError, FileNotFoundError):
            return None

        block_size = stat.f_frsize
        size_limit = stat.f_blocks * block_size
        size_used = (stat.f_blocks - stat.f_bavail) * block_size

        return cls(name, size_used, size_limit)


class IhomeUsage(AbstractFilesystemUsage):
    """Disk quota for the ihome file system on VAST."""

    def __init__(self, name: str, size_used: int, size_limit: int, has_quota: bool = True) -> None:
        """Create a new ihome quota object.

        Args:
            name: The name of the file system.
            size_used: Bytes consumed by the user.
            size_limit: Maximum bytes allowed by the allocation.
            has_quota: Whether a quota is actually configured for this path.
        """

        super().__init__(name, size_used, size_limit)
        self.has_quota = has_quota

    def _verbose_string(self) -> str:
        used = self.convert_size(self.size_used)
        if not self.has_quota:
            return f'-> {self.name}: Bytes Used: {used} ({NO_QUOTA_MSG})'

        limit = self.convert_size(self.size_limit)
        return f'-> {self.name}: Bytes Used: {used}, Byte Limit: {limit}'

    def _short_string(self) -> str:
        used = self.convert_size(self.size_used)
        if not self.has_quota:
            return f'-> {self.name}: {used} / {NO_QUOTA_MSG}'

        limit = self.convert_size(self.size_limit)
        return f'-> {self.name}: {used} / {limit}'

    @classmethod
    def from_path(cls, name: str, path: str) -> IhomeUsage | None:
        """Return a quota object for the given ihome path.

        VAST reports the quota limit as the file system size when a quota is set.
        To detect whether a quota is configured, the reported directory size is
        compared against the /ihome mount point. If they are within 1%, no quota
        is assumed.

        Args:
            name: The name of the file system.
            path: The user's ihome directory path.

        Returns:
            An `IhomeUsage` instance, or None if the path does not exist.
        """

        try:
            stat = os.statvfs(path)
            mount_stat = os.statvfs('/ihome')

        except (OSError, FileNotFoundError):
            return None

        # f_frsize = fragment size (fundamental block size)
        # f_blocks = total blocks
        # f_bavail = free blocks (for non-superuser)
        block_size = stat.f_frsize
        size_limit = stat.f_blocks * block_size
        size_used = (stat.f_blocks - stat.f_bavail) * block_size

        # Compare against mount point to detect if quota is set
        # If the user's directory reports a size within 1% of the mount point,
        # assume no quota is configured for that directory
        mount_size = mount_stat.f_blocks * mount_stat.f_frsize

        if mount_size > 0:
            size_ratio = size_limit / mount_size
            has_quota = not (0.99 <= size_ratio <= 1.01)

        else:
            has_quota = False

        return cls(name, size_used, size_limit, has_quota)


class VastUsage(AbstractFilesystemUsage):
    """Disk quota for VAST project storage (/vast)."""

    def __init__(self, name: str, size_used: int, size_limit: int, has_quota: bool = True) -> None:
        """Create a new VAST quota object.

        Args:
            name: The name of the file system.
            size_used: Bytes consumed.
            size_limit: Maximum bytes allowed by the allocation.
            has_quota: Whether a quota is actually configured for this path.
        """

        super().__init__(name, size_used, size_limit)
        self.has_quota = has_quota

    def _verbose_string(self) -> str:
        used = self.convert_size(self.size_used)
        if not self.has_quota:
            return f'-> {self.name}: Bytes Used: {used} ({NO_QUOTA_MSG})'

        limit = self.convert_size(self.size_limit)
        return f'-> {self.name}: Bytes Used: {used}, Byte Limit: {limit}'

    def _short_string(self) -> str:
        used = self.convert_size(self.size_used)
        if not self.has_quota:
            return f'-> {self.name}: {used} / {NO_QUOTA_MSG}'

        limit = self.convert_size(self.size_limit)
        return f'-> {self.name}: {used} / {limit}'

    @classmethod
    def from_path(cls, name: str, path: str) -> VastUsage | None:
        """Return a quota object for the given VAST path.

        Uses the same heuristic as `IhomeUsage.from_path` to detect whether a
        quota is configured by comparing against the /vast mount point.

        Args:
            name: The name of the file system.
            path: The group's VAST directory path.

        Returns:
            A `VastUsage` instance, or None if the path does not exist.
        """

        try:
            stat = os.statvfs(path)
            mount_stat = os.statvfs('/vast')

        except (OSError, FileNotFoundError):
            return None

        block_size = stat.f_frsize
        size_limit = stat.f_blocks * block_size
        size_used = (stat.f_blocks - stat.f_bavail) * block_size

        # Compare against mount point to detect if quota is set
        mount_size = mount_stat.f_blocks * mount_stat.f_frsize

        if mount_size > 0:
            size_ratio = size_limit / mount_size
            has_quota = not (0.99 <= size_ratio <= 1.01)

        else:
            has_quota = False

        return cls(name, size_used, size_limit, has_quota)


class CrcQuota(BaseParser):
    """Display disk quota usage for a user across CRC file systems."""

    def __init__(self) -> None:
        """Define arguments for the command line interface."""

        super(CrcQuota, self).__init__()
        self.add_argument('user', default=None, nargs='?', help='username to query disk usage for')
        self.add_argument('--verbose', action='store_true', help='use verbose output')

    @staticmethod
    def get_user_info(username: str | None = None) -> tuple[str, int, str, int, str]:
        """Return system identity information for a user.

        Args:
            username: The name of the user to look up (defaults to the current user).

        Returns:
            A tuple of (username, uid, group name, gid, home directory).
        """

        try:
            if username:
                pw_entry = pwd.getpwnam(username)

            else:
                pw_entry = pwd.getpwuid(os.getuid())

        except KeyError:
            sys.exit(f'Could not find quota information for user {username}')

        user = pw_entry.pw_name
        uid = pw_entry.pw_uid
        gid = pw_entry.pw_gid
        homedir = pw_entry.pw_dir

        # Get group name from gid
        import grp
        try:
            group = grp.getgrgid(gid).gr_name

        except KeyError:
            group = str(gid)

        return user, uid, group, gid, homedir

    @staticmethod
    def get_group_quotas(group: str) -> tuple[GenericUsage | VastUsage, ...]:
        """Return quota objects for all group-level storage paths that exist.

        Args:
            group: The name of the group to check quotas for.

        Returns:
            A tuple of quota objects for each storage path that exists.
        """

        all_quotas = (
            GenericUsage.from_path('zfs1', f'/zfs1/{group}'),
            GenericUsage.from_path('zfs2', f'/zfs2/{group}'),
            GenericUsage.from_path('ix', f'/ix/{group}'),
            GenericUsage.from_path('ix1', f'/ix1/{group}'),
            GenericUsage.from_path('ix3', f'/ix3/{group}'),
            VastUsage.from_path('vast', f'/vast/{group}'),
        )

        return tuple(q for q in all_quotas if q is not None)

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application.

        Args:
            args: Parsed command line arguments.
        """

        # Get disk usage information for the given user
        user, uid, group, gid, homedir = self.get_user_info(args.user)

        # Get quota for the user's home directory
        ihome_quota = IhomeUsage.from_path('ihome', homedir)

        # Get quotas for any of the user's shared groups
        group_quotas = self.get_group_quotas(group)

        print(f"User: '{user}'")
        if args.verbose:
            print(f'User ID: {uid}')

        if ihome_quota:
            print(ihome_quota.to_string(args.verbose))

        else:
            print('-> ihome: Unable to retrieve quota information')

        print(f"\nGroup: '{group}'")
        if args.verbose:
            print(f'Group ID: {gid}')

        for quota in group_quotas:
            print(quota.to_string(args.verbose))

        if not group_quotas:
            print(
                'If you need additional storage, you can request up to 5TB on '
                'IX!. Contact CRCD for more details.')
