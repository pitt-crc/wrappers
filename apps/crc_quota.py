"""Command line utility for checking a user's disk usage"""

from __future__ import annotations

import json
import math
import sys
from argparse import Namespace
from typing import Optional, Tuple

from ._base_parser import BaseParser
from ._system_info import Shell


class AbstractFilesystemUsage(object):
    """Base class for building object-oriented representations of file system quotas"""

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

    def to_string(self, verbose=False):
        """Return a string representation of the quota usage

        Args:
            verbose: Return a more detailed representation
        """

        if verbose:
            return self._verbose_string()

        return self._short_string()

    def _verbose_string(self) -> str:
        return "-> {}: Bytes Used: {}, Byte Limit: {}".format(
            self.name,
            self.convert_size(self.size_used),
            self.convert_size(self.size_limit))

    def _short_string(self) -> str:
        return "-> {}: {} / {}".format(
            self.name,
            self.convert_size(self.size_used),
            self.convert_size(self.size_limit)
        )

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
            An instance of the parent class
        """

        df_command = f"df {path}"
        quota_info_list = Shell.run_command(df_command).splitlines()
        if not quota_info_list:
            return None

        result = quota_info_list[1].split()
        return cls(name, int(result[2]) * 1024, int(result[1]) * 1024)


class BeegfsUsage(AbstractFilesystemUsage):
    """Disk storage quota for a BeeGFS file system"""

    def __init__(self, name: str, size_used: int, size_limit: int, chunk_used: int, chunk_limit: int) -> None:
        """Create a new BeeGFS quota from known system metrics

        Args:
            name: Name of the file system (e.g., zfs, ix, home)
            size_used: Disk space used by the user/group
            size_limit: Maximum disk space allowed by the allocation
            chunk_used: Data chunk files used by the user/group
            chunk_limit: Maximum chunks allowed by the allocation
        """

        super(BeegfsUsage, self).__init__(name, size_used, size_limit)
        self.chunk_used = chunk_used
        self.chunk_limit = chunk_limit

    def _verbose_string(self) -> str:
        return "-> {}: Bytes Used: {}, Byte Limit: {}, Chunk Files Used: {}, Chunk File Limit: {}".format(
            self.name,
            self.size_used,
            self.size_limit,
            self.chunk_used,
            self.chunk_limit)

    @classmethod
    def from_group(cls, name: str, group: str) -> Optional[BeegfsUsage]:
        """Return a quota object for a given group name

        Args:
            name: Name of the file system (e.g., zfs, ix, home)
            group: The group to create a quota for

        Returns:
            An instance of the parent class
        """

        allocation_out = Shell.run_command(f"df /bgfs/{group}")
        if len(allocation_out) == 0:
            return None

        quota_info_cmd = f"beegfs-ctl --getquota --gid {group} --csv --storagepoolid=1"
        quota_out = Shell.run_command(quota_info_cmd)
        result = quota_out.splitlines()[1].split(',')
        return cls(name, int(result[2]), int(result[3]), int(result[4]), int(result[5]))


class IhomeUsage(AbstractFilesystemUsage):
    """Disk storage quota for the ihome file system"""

    def __init__(self, name: str, size_used: int, size_limit: int, files: int, physical: int) -> None:
        """Create a new ihome quota from known system metrics

        Args:
            name: Name of the file system (e.g., zfs, ix, home)
            size_used: Disk space used by the user/group
            size_limit: Maximum disk space allowed by the allocation
            files: Number of files written to disk
            physical: Physical size of the data on disk
        """

        super(IhomeUsage, self).__init__(name, size_used, size_limit)
        self.files = files
        self.physical = physical

    def _verbose_string(self) -> str:
        return "-> {}: Logical Bytes Used: {}, Byte Limit: {}, Num Files: {}, Physical Bytes Used: {}".format(
            self.name, self.size_used, self.size_limit, self.files, self.physical)

    @classmethod
    def from_uid(cls, name: str, uid: int) -> Optional[IhomeUsage]:
        """Return a quota object for a given user id

        Args:
            name: Name of the file system (e.g., zfs, ix, home)
            uid: The ID of the user

        Returns:
            An instance of the parent class
        """

        # Get the information from Isilon
        with open("/ihome/crc/scripts/ihome_quota.json", "r") as infile:
            data = json.load(infile)

        persona = f"UID:{uid}"
        for item in data["quotas"]:
            if item["persona"] is not None:
                if item["persona"]["id"] == persona:
                    return cls(name, item["usage"]["logical"], item["thresholds"]["hard"],
                               item["usage"]["inodes"], item["usage"]["physical"])


class CrcQuota(BaseParser):
    """Display a user's disk quota."""

    def __init__(self) -> None:
        """Define arguments for the command line interface"""

        super(CrcQuota, self).__init__()
        self.add_argument('user', default=None, nargs='?', help='username to query disk usage for')
        self.add_argument('--verbose', action='store_true', help='use verbose output')

    @staticmethod
    def get_user_info(username: Optional[str] = None) -> Tuple[str, int, str, int]:
        """Return system IDs for the current user

        Args:
            username: The name of the user to get IDs for (defaults to current user)

        Returns:
            Tuple with the user's name, user ID, group name, and group ID
        """

        username = username or ''
        check_user_cmd = f"id -un {username}"
        user, err = Shell.run_command(check_user_cmd, include_err=True)

        if err:
            sys.exit(f"Could not find quota information for user {username}")

        group = Shell.run_command(f"id -gn {username}")
        uid = Shell.run_command(f"id -u {username}")
        gid = Shell.run_command(f"id -g {username}")

        return user, int(uid), group, int(gid)

    @staticmethod
    def get_group_quotas(group: str) -> Tuple[GenericUsage]:
        """Return quota information for the given group

        Args:
            group: The name of the group

        Returns:
            A tuple of ``Quota`` objects
        """

        zfs1_quota = GenericUsage.from_path('zfs1', f'/zfs1/{group}')
        zfs2_quota = GenericUsage.from_path('zfs2', f'/zfs2/{group}')
        bgfs_quota = BeegfsUsage.from_group('beegfs', group)
        ix_quota = GenericUsage.from_path('ix', f'/ix/{group}')

        # Only return quotas that exist for the given group (i.e., objects that are not None)
        all_quotas = (zfs1_quota, zfs2_quota, bgfs_quota, ix_quota)
        return tuple(filter(None, all_quotas))

    def app_logic(self, args: Namespace) -> None:
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        # Get disk usage information for the given user
        user, uid, group, gid = self.get_user_info(args.user)
        ihome_quota = IhomeUsage.from_uid('ihome', uid)
        supp_quotas = self.get_group_quotas(group)

        print(f"User: '{user}'")
        if args.verbose:
            print(f'User ID: {uid}')

        if ihome_quota:
            print(ihome_quota.to_string(args.verbose))

        else:
            print('-> None')

        print(f"\nGroup: '{group}'")
        if args.verbose:
            print(f'Group ID: {gid}')

        for quota in supp_quotas:
            print(quota.to_string(args.verbose))

        if not supp_quotas:
            print(
                'If you need additional storage, you can request up to 5TB on '
                'BGFS, ZFS or IX!. Contact CRC for more details.')
