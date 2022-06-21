#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""Command line utility for checking a user's disk usage"""

import json
import math
import sys
from shlex import split
from subprocess import Popen, PIPE

from _base_parser import BaseParser


class Quota(object):
    """Class to represent a quota"""

    def __init__(self, system, name, id, size_used, size_limit):
        self.name = name
        self.system = system
        self.id = id
        self.size_used = self.convert_size(int(size_used))
        self.size_limit = self.convert_size(int(size_limit))

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

    @staticmethod
    def from_path(group, gid, path, system):
        command = "df {}".format(path)
        command_out, _ = run_command(command)
        quota_info = command_out.strip().splitlines()

        if quota_info:
            result = quota_info[1].split()
            return Quota(system, group, gid, int(result[2]) * 1024, int(result[1]) * 1024)

    @staticmethod
    def from_uid(user, uid):
        # Get the information from Isilon
        persona = "UID:{}".format(uid)

        with open("/ihome/crc/scripts/ihome_quota.json", "r") as f:
            data = json.load(f)

        for item in data["quotas"]:
            if item["persona"] is not None:
                if item["persona"]["id"] == persona:
                    return Quota(user, uid, item["usage"]["logical"], item["thresholds"]["hard"], item["usage"]["inodes"])

        return None

    def __str__(self):
        return "Name: {}, ID: {}, Bytes Used: {}, Byte Limit: {}".format(
            self.name, self.id, self.size_used, self.size_limit)


def run_command(command):
    p = Popen(split(command), stdout=PIPE, stderr=PIPE)
    return p.communicate()


class CrcQuota(BaseParser):
    """Commandline tool for fetching a user's disk quota"""

    def __init__(self):
        """Define arguments for the command line interface"""

        super(CrcQuota, self).__init__()
        self.add_argument('-u', '--user', default=None, help='username of quota to query')
        self.add_argument('--verbose', action='store_true', help='verbose quota output')

    def get_user_info(self, user=None):
        """Return system IDs for the current user

        Args:
            user: The name of the user to get IDs for (defaults to current user)

        Returns:

        """

        if user is None:
            user = self.run_command("id -un")
            group = self.run_command("id -gn")
            uid = self.run_command("id -u")
            gid = self.run_command("id -g")

        elif len(run_command("id -un {}".format(user))[1]) > 0:
            sys.exit("Could not find quota information for user {}".format(user))

        else:
            user = self.run_command("id -un {}".format(user))
            group = self.run_command("id -gn {}".format(user))
            uid = self.run_command("id -u {}".format(user))
            gid = self.run_command("id -g {}".format(user))

        return gid, group, uid, user

    def get_quota_info(self, group, gid):
        """Return quota information for the given group

        Args:
            group: The name of the group
            gid: The system id of the group

        Returns:
            A tuple of ``Quota`` objects
        """

        bgfs_quota = Quota.from_path(group, gid, '/bgfs/{}'.format(group), 'bgfs')
        zfs1_quota = Quota.from_path(group, gid, '/zfs1/{}'.format(group), 'zfs1')
        zfs2_quota = Quota.from_path(group, gid, '/zfs2/{}'.format(group), 'zfs2')
        ix_quota = Quota.from_path(group, gid, '/ix/{}'.format(group), 'ix')

        all_quotas = (bgfs_quota, zfs1_quota, zfs2_quota, ix_quota)
        return tuple(quota for quota in all_quotas if quota is not None)

    def print_quota(self, quota, verbose=False):

        if verbose:
            print('-> {}: {}'.format(quota.system, quota))

        else:
            print('-> {}: {} / {}'.format(quota.system, quota.size_used, quota.size_limit))

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        gid, group, uid, user = self.get_user_info(args.user)

        # Get disk usage information for each file system
        ihome_quota = IhomeQuota.from_uid(user, uid)
        disk_quotas = self.get_quota_info(group, gid)

        print("User: '{}'".format(user))
        if ihome_quota is None:
            print('-> ihome: NONE')

        else:
            self.print_quota(quota, args.verbose)

        print("Group: '{}'".format(group))
        if not disk_quotas:
            print('If you need additional storage, you can request up to 5TB on BGFS, ZFS or IX!. Contact CRC for more details.')

        for quota in disk_quotas:
            if quota is None:
                continue

            self.print_quota(quota, args.verbose)


if __name__ == "__main__":
    CrcQuota().execute()
