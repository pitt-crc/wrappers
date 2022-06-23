#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""Command line utility for checking a user's disk usage"""

import abc
import json
import math
import sys
from shlex import split
from subprocess import Popen, PIPE

from _base_parser import BaseParser


def run_command(command):
    p = Popen(split(command), stdout=PIPE, stderr=PIPE)
    return p.communicate()[0].strip()


class AbstractQuota(object):
    """Base class for building OO representations of file system quotas"""

    def __init__(self, name, size_used, size_limit):
        """Create a new quota using known disk usage data

        Args:
            size_used: Disk space used by the user/group
            size_limit: Maximum disk space allocated to a user/group
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

    def _verbose_string(self):
        return "Name: {}, ID: {}, Bytes Used: {}, Byte Limit: {}".format(
            self.name,
            self.id,
            self.convert_size(self.size_used),
            self.convert_size(self.size_limit))

    def _short_string(self):
        return "-> {}: {} / {}".format(
            self.name,
            self.convert_size(self.size_used),
            self.convert_size(self.size_limit)
        )

    @staticmethod
    def convert_size(size):
        """Convert the given number of bytes to a human-readable string

        Args:
            size: An integer number of bytes

        Returns:
             A string representation of the given size with units
        """

        if size == 0:
            return '0B'

        size_units = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
        i = int(math.floor(math.log(size, 1024)))
        p = math.pow(1024, i)
        s = round(size / p, 2)
        return '%s %s' % (s, size_units[i])


class GenericQuota(AbstractQuota):
    """Disk storage quota for a generic file system"""

    @classmethod
    def from_path(cls, name, path):
        """Return a quota object for a given file path

        Args:
            name: Name of the file system (e.g., zfs, ix, home)
            path: The file path for create a quota for

        Returns:
            An instance of the parent class
        """

        df_command = "df {}".format(path)
        quota_info_list = run_command(df_command).splitlines()
        if not quota_info_list:
            return None

        result = quota_info_list[1].split()
        return cls(name, int(result[2]) * 1024, int(result[1]) * 1024)


class BeegfsQuota(AbstractQuota):
    """Disk storage quota for a BeeGFS file system"""

    def __init__(self, name, size_used, size_limit, chunk_used, chunk_limit):
        super(BeegfsQuota, self).__init__(name, size_used, size_limit)
        self.chunk_used = chunk_used
        self.chunk_limit = chunk_limit

    @classmethod
    def from_group(cls, group):
        quota_out, quota_err = run_command("beegfs-ctl --getquota --gid {} --csv --storagepoolid=1".format(group))
        result = quota_out.splitlines()[1].split(',')
        return cls(result[2], result[3], result[4], result[5])


class IsilonQuota(AbstractQuota):
    """Disk storage quota for the ihome file system"""

    def __init__(self, name, size_used, size_limit, inodes, physical):
        super(IsilonQuota, self).__init__(name, size_used, size_limit)
        self.inodes = inodes
        self.physical = physical

    @classmethod
    def from_uid(cls, name, uid):
        # Get the information from Isilon
        with open("/ihome/crc/scripts/ihome_quota.json", "r") as f:
            data = json.load(f)

        persona = "UID:{}".format(uid)
        for item in data["quotas"]:
            if item["persona"] is not None:
                if item["persona"]["id"] == persona:
                    return cls(name, item["usage"]["logical"], item["thresholds"]["hard"], item["usage"]["inodes"], item["usage"]["physical"])


class CrcQuota(BaseParser):
    """Commandline tool for fetching a user's disk quota"""

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcQuota, self).__init__()
        self.add_argument('-u', '--user', default=None, help='username of quota to query')
        self.add_argument('--verbose', action='store_true', help='verbose quota output')

    def get_user_info(self, username=None):
        """Return system IDs for the current user

        Args:
            username: The name of the user to get IDs for (defaults to current user)

        Returns:

        """

        username = username or ''
        check_user_cmd = "id -un {}".format(username)
        user, err = self.run_command(check_user_cmd, include_err=True)

        if err:
            sys.exit("Could not find quota information for user {}".format(username))

        group = self.run_command("id -gn {}".format(username))
        uid = self.run_command("id -u {}".format(username))
        gid = self.run_command("id -g {}".format(username))

        return gid, group, uid, user

    @staticmethod
    def get_group_quotas(group):
        """Return quota information for the given group

        Args:
            group: The name of the group

        Returns:
            A tuple of ``Quota`` objects
        """

        bgfs_quota = GenericQuota.from_path('bgfs', '/bgfs/{}'.format(group))
        zfs1_quota = GenericQuota.from_path('zfs1', '/zfs1/{}'.format(group))
        zfs2_quota = GenericQuota.from_path('zfs2', '/zfs2/{}'.format(group))
        ix_quota = GenericQuota.from_path('ix', '/ix/{}'.format(group))

        # Only return quotas that exist for the given group
        all_quotas = (bgfs_quota, zfs1_quota, zfs2_quota, ix_quota)
        return tuple(filter(None, all_quotas))

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        # Get disk usage information for the given user
        gid, group, uid, user = self.get_user_info(args.user)
        ihome_quota = IsilonQuota.from_uid('ihome', uid)
        supp_quotas = self.get_group_quotas(group)

        print("User: '{}'".format(user))
        print(ihome_quota.to_string(args.verbose))

        print("\nGroup: '{}'".format(group))
        for quota in supp_quotas:
            print(quota.to_string(args.verbose))

        if not supp_quotas:
            print('If you need additional storage, you can request up to 5TB on BGFS, ZFS or IX!. Contact CRC for more details.')


if __name__ == "__main__":
    CrcQuota().execute()
