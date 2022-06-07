#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""Command line utility for checking a user's disk usage"""

import json
import math
import sys
from os import path
from shlex import split
from subprocess import Popen, PIPE

from _base_parser import BaseParser

__version__ = BaseParser.get_semantic_version()
__app_name__ = path.basename(__file__)


class Quota(object):
    """Class to represent a quota"""

    def __init__(self, system, name, id, size_used, size_limit):
        self.name = name
        self.system = system
        self.id = id
        self.size_used = float(size_used)
        self.size_limit = float(size_limit)

    def __str__(self):
        return "Name: {}, ID: {}, Bytes Used: {}, Byte Limit: {}".format(
            self.name, self.id, self.size_used, self.size_limit)


class BeegfsQuota(Quota):
    """Class to represent a BeeGFS quota"""

    def __init__(self, name, id, size_used, size_limit, chunk_used, chunk_limit):
        super(BeegfsQuota, self).__init__('beegfs', name, id, size_used, size_limit)
        self.chunk_used = chunk_used
        self.chunk_limit = chunk_limit

    def __str__(self):
        return "Name: {}, ID: {}, Bytes Used: {}, Byte Limit: {}, Chunk Files Used: {}, Chunk File Limit: {}".format(
            self.name, self.id, self.size_used, self.size_limit, self.chunk_used, self.chunk_limit)


class IhomeQuota(Quota):
    """Class to represent an iHome quota"""

    def __init__(self, name, id, size_used, size_limit, inodes, physical):
        super(IhomeQuota, self).__init__('ihome', name, id, size_used, size_limit)
        self.inodes = inodes
        self.physical = physical

    def __str__(self):
        return "Name: {}, ID: {}, Logical Bytes Used: {}, Byte Limit: {}, Num Files: {}, Physical Bytes Used: {}".format(
            self.name, self.id, self.size_used, self.size_limit, self.inodes, self.physical)


def beegfs_get_quota_from_gid(group):
    """Get BeeGFS quota for a given GID"""

    allocation_out, allocation_err = run_command("df /bgfs/{}".format(group))

    if len(allocation_out) == 0:
        return None

    quota_out, quota_err = run_command("beegfs-ctl --getquota --gid {} --csv --storagepoolid=1".format(group))
    result = quota_out.splitlines()[1].split(',')
    return BeegfsQuota(result[0], result[1], result[2], result[3], result[4], result[5])


def zfs_get_quota_from_gid(group, gid):
    zfs1_quota = run_command("df /zfs1/{}".format(group))[0].strip()
    zfs1_quota = zfs1_quota.splitlines()

    if len(zfs1_quota) == 0:
        zfs1_quota = None
    else:
        result = zfs1_quota[1].split()
        zfs1_quota = Quota('zfs1', group, gid, int(result[2]) * 1024, int(result[1]) * 1024)

    zfs2_quota = run_command("df /zfs2/{}".format(group))[0].strip()
    zfs2_quota = zfs2_quota.splitlines()

    if len(zfs2_quota) == 0:
        zfs2_quota = None
    else:
        result = zfs2_quota[1].split()
        zfs2_quota = Quota('zfs2', group, gid, int(result[2]) * 1024, int(result[1]) * 1024)

    return zfs1_quota, zfs2_quota


def ihome_get_quota_from_uid(user, uid):
    # Get the information from Isilon
    persona = "UID:{}".format(uid)

    with open("/ihome/crc/scripts/ihome_quota.json", "r") as f:
        data = json.load(f)

    for item in data["quotas"]:
        if item["persona"] is not None:
            if item["persona"]["id"] == persona:
                return IhomeQuota(user, uid, item["usage"]["logical"], item["thresholds"]["hard"], item["usage"]["inodes"], item["usage"]["physical"])

    return None


def ix_get_quota(group, gid):
    ix_quota = run_command("df /ix/{}".format(group))[0].strip()
    ix_quota = ix_quota.splitlines()

    if len(ix_quota) == 0:
        ix_quota = None
    else:
        result = ix_quota[1].split()
        ix_quota = Quota('ix', group, gid, int(result[2]) * 1024, int(result[1]) * 1024)

    return ix_quota


def convert_size(size):
    if size == 0:
        return '0B'

    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return '%s %s' % (s, size_name[i])


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

    def app_logic(self, args):
        """Logic to evaluate when executing the application

        Args:
            args: Parsed command line arguments
        """

        if args.user is None:
            user = self.run_command("id -un")
            group = self.run_command("id -gn")
            uid = self.run_command("id -u")
            gid = self.run_command("id -g")
        else:
            if len(run_command("id -un {}".format(args.user))[1]) > 0:
                sys.exit("I don't know who {} is!".format(args.user))

            user = self.run_command("id -un {}".format(args.user))
            group = self.run_command("id -gn {}".format(args.user))
            uid = self.run_command("id -u {}".format(args.user))
            gid = self.run_command("id -g {}".format(args.user))

        bgfs_quota = beegfs_get_quota_from_gid(group)
        zfs1_quota, zfs2_quota = zfs_get_quota_from_gid(group, gid)
        ihome_quota = ihome_get_quota_from_uid(user, uid)
        ix_quota = ix_get_quota(group, gid)

        print("User: '{}'".format(user))
        if ihome_quota is None:
            print("-> ihome: NONE")

        else:
            if args.verbose:
                print("-> ihome: {}".format(ihome_quota))
            else:
                print("-> ihome: {} / {}".format(convert_size(float(ihome_quota.size_used)), convert_size(float(ihome_quota.size_limit))))

        print("")

        print("Group: '{}'".format(group))
        if not any((zfs1_quota, zfs2_quota, bgfs_quota, ix_quota)):
            print("If you need additional storage, you can request up to 5TB on BGFS, ZFS or IX!. Contact CRC for more details.")

        for quota in (zfs1_quota, zfs2_quota, bgfs_quota, ix_quota):
            if quota is None:
                continue

            if args.verbose:
                print("-> {}: {}".format(quota.system, quota))

            else:
                print("-> {}: {} / {}".format(quota.system, convert_size(quota.size_used), convert_size(quota.size_limit)))


if __name__ == "__main__":
    CrcQuota().execute()
