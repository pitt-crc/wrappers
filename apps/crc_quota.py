"""Command line utility for checking a user's disk usage.

This application prints a user's disk usage on multiple CRC file systems.
Disk usage is determined using the ``df`` command line utility, which reports
quota limits as the filesystem size when quotas are set on VAST.

The file system paths (and types) are hard coded in this application.
To modify what file systems are examined by the application, see the
``CrcQuota.app_logic`` method.
"""

from __future__ import annotations

import math
import os
import pwd
import sys
from argparse import Namespace
from typing import Optional, Tuple

from .utils.cli import BaseParser
from .utils.system_info import Shell


NO_QUOTA_MSG = "No Quota Found, Please contact the CRCD Team to fix this!"


class AbstractFilesystemUsage:
    """Base class for building object-oriented representations of file system quotas."""

    def __init__(self, name: str, size_used: int, size_limit: int) -> None:
        """Create a new quota from known system metrics

        Args:
            name: Name of the file system (e.g., zfs, ix, home)
            size_used: Disk space used by the user/group
            size_limit: Maximum disk space allowed by the allocation
        """

        self.name = name
        self.size_used = size_used
        self.size_limit = size_limit

    def to_string(self, verbose: bool = False) -> str:
        """Return a string representation of the quota usage

        Args:
            verbose: Return a more detailed representation

        Returns:
            Human readable quota usage information
        """

        if verbose:
            return self._verbose_string()

        return self._short_string()

    def _verbose_string(self) -> str:
        used = self.convert_size(self.size_used)
        limit = self.convert_size(self.size_limit)
        return f"-> {self.name}: Bytes Used: {used}, Byte Limit: {limit}"

    def _short_string(self) -> str:
        used = self.convert_size(self.size_used)
        limit = self.convert_size(self.size_limit)
        return f"-> {self.name}: {used} / {limit}"

    @staticmethod
    def convert_size(size: int) -> str:
        """Convert the given number of bytes to a human-readable string

        Args:
            size: An integer number of bytes

        Returns:
             A string representation of the given size with units
        """

        if size == 0:
            return '0.0 B'

        size_units = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')

        base_2_power = int(math.floor(math.log(size, 1024)))
        conversion_factor = math.pow(1024, base_2_power)
        final_size = round(size / conversion_factor, 2)
        return f'{final_size} {size_units[base_2_power]}'


class GenericUsage(AbstractFilesystemUsage):
    """Disk storage quota for a generic file system"""

    @classmethod
    def from_path(cls, name: str, path: str) -> Optional[GenericUsage]:
        """Return a quota object for a given file path

        Args:
            name: Name of the file system (e.g., zfs, ix, home)
            path: The file path for create a quota for

        Returns:
            An instance of the parent class or None if the allocation does not exist
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
    """Disk storage quota for the ihome file system on VAST."""

    def __init__(self, name: str, size_used: int, size_limit: int, has_quota: bool = True) -> None:
        """Create a new ihome quota from known system metrics

        Args:
            name: Name of the file system (e.g., ihome)
            size_used: Disk space used by the user
            size_limit: Maximum disk space allowed by the allocation
            has_quota: Whether a quota is actually set for this path
        """

        super(IhomeUsage, self).__init__(name, size_used, size_limit)
        self.has_quota = has_quota

    def _verbose_string(self) -> str:
        used = self.convert_size(self.size_used)
        if not self.has_quota:
            return f"-> {self.name}: Bytes Used: {used} ({NO_QUOTA_MSG})"

        limit = self.convert_size(self.size_limit)
        return f"-> {self.name}: Bytes Used: {used}, Byte Limit: {limit}"

    def _short_string(self) -> str:
        used = self.convert_size(self.size_used)
        if not self.has_quota:
            return f"-> {self.name}: {used} / {NO_QUOTA_MSG}"

        limit = self.convert_size(self.size_limit)
        return f"-> {self.name}: {used} / {limit}"

    @classmethod
    def from_path(cls, name: str, path: str) -> Optional[IhomeUsage]:
        """Return a quota object for a given file path using os.statvfs.

        VAST reports the quota limit as the filesystem size when a quota is set.
        If no quota is set, it reports the full filesystem size.

        To detect if a quota is set, we compare the reported size of the user's
        directory against the mount point. If they are within 1% of each other,
        we assume no quota is configured.

        Args:
            name: Name of the file system (e.g., ihome)
            path: The file path to check quota for

        Returns:
            An instance of IhomeUsage or None if the path does not exist
        """

        try:
            stat = os.statvfs(path)
            mount_stat = os.statvfs("/ihome")
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
    """Disk storage quota for VAST project storage (/vast)."""

    def __init__(self, name: str, size_used: int, size_limit: int, has_quota: bool = True) -> None:
        """Create a new VAST quota from known system metrics

        Args:
            name: Name of the file system (e.g., vast)
            size_used: Disk space used
            size_limit: Maximum disk space allowed by the allocation
            has_quota: Whether a quota is actually set for this path
        """

        super(VastUsage, self).__init__(name, size_used, size_limit)
        self.has_quota = has_quota

    def _verbose_string(self) -> str:
        used = self.convert_size(self.size_used)
        if not self.has_quota:
            return f"-> {self.name}: Bytes Used: {used} ({NO_QUOTA_MSG})"

        limit = self.convert_size(self.size_limit)
        return f"-> {self.name}: Bytes Used: {used}, Byte Limit: {limit}"

    def _short_string(self) -> str:
        used = self.convert_size(self.size_used)
        if not self.has_quota:
            return f"-> {self.name}: {used} / {NO_QUOTA_MSG}"

        limit = self.convert_size(self.size_limit)
        return f"-> {self.name}: {used} / {limit}"

    @classmethod
    def from_path(cls, name: str, path: str) -> Optional[VastUsage]:
        """Return a quota object for a given file path using os.statvfs.

        VAST reports the quota limit as the filesystem size when a quota is set.
        If no quota is set, it reports the full filesystem size.

        Args:
            name: Name of the file system (e.g., vast)
            path: The file path to check quota for

        Returns:
            An instance of VastUsage or None if the path does not exist
        """

        try:
            stat = os.statvfs(path)
            mount_stat = os.statvfs("/vast")
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
    """Display a user's disk quota."""

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcQuota, self).__init__()
        self.add_argument('user', default=None, nargs='?', help='username to query disk usage for')
        self.add_argument('--verbose', action='store_true', help='use verbose output')

    @staticmethod
    def get_user_info(username: Optional[str] = None) -> Tuple[str, int, str, int, str]:
        """Return system IDs for the current user

        Args:
            username: The name of the user to get IDs for (defaults to current user)

        Returns:
            Tuple with the user's name, user ID, group name, group ID, and home directory
        """

        try:
            if username:
                pw_entry = pwd.getpwnam(username)
            else:
                pw_entry = pwd.getpwuid(os.getuid())
        except KeyError:
            sys.exit(f"Could not find quota information for user {username}")

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
    def get_group_quotas(group: str) -> Tuple[GenericUsage, ...]:
        """Return quota information for the given group

        Args:
            group: The name of the group

        Returns:
            A tuple of ``Quota`` objects
        """

        zfs1_quota = GenericUsage.from_path('zfs1', f'/zfs1/{group}')
        zfs2_quota = GenericUsage.from_path('zfs2', f'/zfs2/{group}')
        ix_quota = GenericUsage.from_path('ix', f'/ix/{group}')
        ix1_quota = GenericUsage.from_path('ix1', f'/ix1/{group}')
        ix3_quota = GenericUsage.from_path('ix3', f'/ix3/{group}')
        vast_quota = VastUsage.from_path('vast', f'/vast/{group}')

        # Only return quotas that exist for the given group (i.e., objects that are not None)
        all_quotas = (zfs1_quota, zfs2_quota, ix_quota, ix1_quota, ix3_quota, vast_quota)
        return tuple(filter(None, all_quotas))

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        # Get disk usage information for the given user
        user, uid, group, gid, homedir = self.get_user_info(args.user)

        # Get ihome quota using df against the user's actual home directory
        ihome_quota = IhomeUsage.from_path('ihome', homedir)

        supp_quotas = self.get_group_quotas(group)

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

        for quota in supp_quotas:
            print(quota.to_string(args.verbose))

        if not supp_quotas:
            print(
                'If you need additional storage, you can request up to 5TB on '
                'IX!. Contact CRCD for more details.')

