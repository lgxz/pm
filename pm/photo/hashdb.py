#!/usr/bin/env python
# coding: utf-8

"""维护文件Hash列表文件"""

import os
from sys import intern


class HashDB():
    """Hash DB"""

    def __init__(self, hashfile):
        """Init"""
        self.hashfile = hashfile
        self.hash2path = {}
        self.path2hash = {}
        self.dirty = False
        self.load()

    def add(self, path, md5, overwrite=False):
        """Add a path with/witout hash"""
        if path in self.path2hash and not overwrite:
            return False

        md5 = intern(md5)
        path = intern(path)
        self.path2hash[path] = md5
        self.hash2path[md5] = path
        self.dirty = True
        return True

    def remove(self, path):
        """Remove a path"""
        try:
            md5 = self.path2hash.pop(path)
        except KeyError:
            return False

        del self.hash2path[md5]
        self.dirty = True
        return True

    def rename(self, src, dst, overwrite=False):
        """Rename src to dst"""
        if not overwrite and dst in self.path2hash:
            return False

        try:
            md5 = self.path2hash.pop(src)
        except KeyError:
            return False

        self.path2hash[dst] = md5
        self.hash2path[md5] = dst
        self.dirty = True
        return True

    def exists(self, md5):
        """一个Hash是否存在"""
        return md5 in self.hash2path

    def paths(self):
        """Paths"""
        return self.path2hash.keys()

    def load(self):
        """Load all items"""
        hash2path = {}
        path2hash = {}
        if self.hashfile.exists():
            for line in self.hashfile.open():
                line = line.strip()
                if not line:
                    continue
                md5, path = line.strip().split(maxsplit=1)
                assert md5 not in hash2path
                md5 = intern(md5)
                path = intern(path)
                hash2path[md5] = path
                path2hash[path] = md5

        self.hash2path = hash2path
        self.path2hash = path2hash
        return hash2path, path2hash

    def save(self):
        """Save to file"""
        if not self.dirty:
            return True

        tmpfile = str(self.hashfile) + ".tmp"
        with open(tmpfile, 'w') as fp_:
            for path, md5 in self.path2hash.items():
                fp_.write("%s %s\n" % (md5, path))

        os.rename(tmpfile, self.hashfile)
        self.dirty = False
        return True
