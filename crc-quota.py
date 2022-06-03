#!/usr/bin/env /ihome/crc/wrappers/py_wrap.sh
"""crc-quota.py
Usage:
    crc-quota.py
    crc-quota.py -u <USER> | --user <USER> [-v | --verbose]
    crc-quota.py -v | --verbose
    crc-quota.py -h | --help
    crc-quota.py --version

Options:
    -u USER --user USER         Username of quota to query
    -v --verbose                Verbose quota output                    
    -h --help                   Print this screen and exit
    --version                   Print the version of crc-quota.py
"""

import json
import math
import sys
from os import path
from shlex import split
from subprocess import Popen, PIPE

from docopt import docopt

from _base_parser import BaseParser

__version__ = BaseParser.get_semantic_version()
__app_name__ = path.basename(__file__)


class Quota:
    """Class to represent a quota"""

    def __init__(self, name, id, size_used, size_limit):
        self.name = name
        self.id = id
        self.size_used = size_used
        self.size_limit = size_limit

    def __str__(self):
        return "Name: {}, ID: {}, Bytes Used: {}, Byte Limit: {}".format(
            self.name, self.id, self.size_used, self.size_limit)

    def __repr__(self):
        return "<{} instance at {}: {}>".format(self.__class__, id(self), self.__dict__)


class BeegfsQuota(Quota):
    """Class to represent a BeeGFS quota"""

    def __init__(self, name, id, size_used, size_limit, chunk_used, chunk_limit):
        self.name = name
        self.id = id
        self.size_used = size_used
        self.size_limit = size_limit
        self.chunk_used = chunk_used
        self.chunk_limit = chunk_limit

    def __str__(self):
        return "Name: {}, ID: {}, Bytes Used: {}, Byte Limit: {}, Chunk Files Used: {}, Chunk File Limit: {}".format(
            self.name, self.id, self.size_used, self.size_limit, self.chunk_used, self.chunk_limit)


class IhomeQuota(Quota):
    """Class to represent an iHome quota"""

    def __init__(self, name, id, size_used, size_limit, inodes, physical):
        self.name = name
        self.id = id
        self.size_used = size_used
        self.size_limit = size_limit
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
    else:
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
        zfs1_quota = Quota(group, gid, int(result[2]) * 1024, int(result[1]) * 1024)

    zfs2_quota = run_command("df /zfs2/{}".format(group))[0].strip()
    zfs2_quota = zfs2_quota.splitlines()

    if len(zfs2_quota) == 0:
        zfs2_quota = None
    else:
        result = zfs2_quota[1].split()
        zfs2_quota = Quota(group, gid, int(result[2]) * 1024, int(result[1]) * 1024)

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
        ix_quota = Quota(group, gid, int(result[2]) * 1024, int(result[1]) * 1024)

    return ix_quota


def convert_size(size):
    if (size == 0):
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return '%s %s' % (s, size_name[i])


def run_command(command):
    p = Popen(split(command), stdout=PIPE, stderr=PIPE)
    return p.communicate()


def main():
    arguments = docopt(__doc__, version='{} version {}'.format(__app_name__, __version__))

    if arguments['--user'] is None:
        USER = run_command("id -un")[0].strip()
        GROUP = run_command("id -gn")[0].strip()

        UID = run_command("id -u")[0].strip()
        GID = run_command("id -g")[0].strip()
    else:
        if len(run_command("id -un {}".format(arguments['--user']))[1]) > 0:
            sys.exit("I don't know who {} is!".format(arguments['--user']))
        USER = run_command("id -un {}".format(arguments['--user']))[0].strip()
        GROUP = run_command("id -gn {}".format(arguments['--user']))[0].strip()

        UID = run_command("id -u {}".format(arguments['--user']))[0].strip()
        GID = run_command("id -g {}".format(arguments['--user']))[0].strip()

    bgfs_quota = beegfs_get_quota_from_gid(GROUP)
    zfs1_quota, zfs2_quota = zfs_get_quota_from_gid(GROUP, GID)
    ihome_quota = ihome_get_quota_from_uid(USER, UID)
    ix_quota = ix_get_quota(GROUP, GID)

    print("User: '{}'".format(USER))
    if ihome_quota is None:
        print("-> ihome: NONE")
    else:
        if arguments['--verbose'] is True:
            print("-> ihome: {}".format(ihome_quota))
        else:
            print("-> ihome: {} / {}".format(convert_size(float(ihome_quota.size_used)), convert_size(float(ihome_quota.size_limit))))

    print("")

    print("Group: '{}'".format(GROUP))
    if zfs1_quota is None and zfs2_quota is None and bgfs_quota is None and ix_quota is None:
        print("If you need additional storage, you can request up to 5TB on BGFS, ZFS or IX!. Contact CRC for more details.")

    if zfs1_quota is not None:
        if arguments['--verbose'] is True:
            print("-> zfs1: {}".format(zfs1_quota))
        else:
            print("-> zfs1: {} / {}".format(convert_size(float(zfs1_quota.size_used)), convert_size(float(zfs1_quota.size_limit))))

    if zfs2_quota is not None:
        if arguments['--verbose'] is True:
            print("-> zfs2: {}".format(zfs2_quota))
        else:
            print("-> zfs2: {} / {}".format(convert_size(float(zfs2_quota.size_used)), convert_size(float(zfs2_quota.size_limit))))

    if bgfs_quota is not None:
        if arguments['--verbose'] is True:
            print("-> bgfs: {}".format(bgfs_quota))
        else:
            print("-> bgfs: {} / {}".format(convert_size(float(bgfs_quota.size_used)), convert_size(float(bgfs_quota.size_limit))))

    if ix_quota is not None:
        if arguments['--verbose'] is True:
            print("-> ix: {}".format(ix_quota))
        else:
            print("-> ix: {} / {}".format(convert_size(float(ix_quota.size_used)), convert_size(float(ix_quota.size_limit))))


if __name__ == "__main__":
    main()
