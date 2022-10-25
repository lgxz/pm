#!/usr/bin/env python
# coding: utf-8

"""照片库实现.

所有对外的参数，如果是路径，都需要传入 Path 对象
"""

import os
import shutil
import hashlib
from pathlib import Path
from collections import Counter

from pm import RunMode
from .hashdb import HashDB


class PhotoHome():
    """照片库."""
    HASH_FILE = ".hash"
    MAX_NO = 100

    def __init__(self, home):
        """Init with path."""
        self.home = home
        self.hashdb = HashDB(self.home / self.HASH_FILE)

    def _list_dir(self):
        """列出目录下所有文件."""
        files = []
        cwd = Path.cwd()
        os.chdir(self.home)
        for root, dirs, names in os.walk('.'):
            if not names and not dirs:
                try:
                    print('XXXXX', root)
                    os.rmdir(root)
                except OSError:
                    pass

            for name in names:
                path = os.path.join(root, name)
                if name == '.DS_Store':
                    try:
                        os.unlink(path)
                    except OSError:
                        pass
                if not name.startswith('.'):
                    files.append(path[2:])

        os.chdir(cwd)
        return files

    def _dt2path(self, dt_, suffix):
        """根据 datetime 对象得到对应的文件路径."""
        subdir = dt_.date().strftime("%Y/%m/%d")
        name = dt_.time().strftime("%H%M%S")

        apath = self.home / subdir
        if suffix == '.jpeg':
            suffix = '.jpg'

        for i in range(self.MAX_NO):
            dst = apath / ("%s_%d%s" % (name, i, suffix))
            if not dst.exists():
                return dst
        return None

    def add_file(self, src, dt_, overwrite=False):
        """Add a file."""
        try:
            md5 = hashlib.md5(src.read_bytes()).hexdigest()
        except FileNotFoundError:
            return 'md5'

        if self.hashdb.exists(md5) and not overwrite:
            return 'dupe'

        dst = self._dt2path(dt_, src.suffix.lower())
        if not dst:
            return 'coll'

        if RunMode.verbose:
            print(f"ADD {src} to {dst}")

        if RunMode.test:
            return None

        dst.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        shutil.copy2(src, dst)

        dst = dst.relative_to(self.home)
        if not self.hashdb.add(str(dst), md5, overwrite):
            return 'add'
        return None

    def move_file(self, path, dt_):
        """Move file to new locaton according dt_."""
        newpath = self._dt2path(dt_, path.suffix)
        if not newpath:
            return 'coll'

        if newpath.parent == path.parent and newpath.stem[:-2] == path.stem[:-2]:
            return 'same'

        new_rpath = str(newpath.relative_to(self.home))
        old_rpath = str(path.relative_to(self.home))
        if RunMode.verbose:
            print(f"Moving {old_rpath} to {new_rpath}")

        if RunMode.test:
            return None

        newpath.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.rename(newpath)
        if not self.hashdb.rename(old_rpath, new_rpath):
            newpath.rename(path)
            return 'rename'
        return None

    def stat_suffix(self):
        """统计文件扩展名."""
        counts = Counter()
        for path in self.hashdb.paths():
            suffix = path.rsplit('.', 1)[1]
            counts[suffix] += 1
        return counts

    def sync(self):
        """同步Hash文件和目录."""
        paths = set(self._list_dir())
        files = set(self.hashdb.paths())

        removed = files - paths
        if removed:
            for path in removed:
                if RunMode.verbose:
                    print(f"File {path} has been removed")
                self.hashdb.remove(path)

        added = paths - files
        if added:
            for path in added:
                print(f"W: unknown file {path}")

        return len(removed), len(added)

    def __del__(self):
        if not RunMode.test:
            self.hashdb.save()
