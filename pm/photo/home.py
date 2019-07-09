#!/usr/bin/env python
# coding: utf-8

"""照片库"""

import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from collections import Counter

from pm import RunMode


class PhotoHome():
    """照片库"""
    HASH_FILE = ".hash"
    MAX_NO = 100

    def __init__(self, home):
        """Init with path"""
        self.home = Path(home).expanduser().resolve(True)
        self.hashfile = self.home / self.HASH_FILE
        self.hash2path = {}
        self.path2hash = {}
        self.dirty = False
        self._hash_load()

    def _hash_load(self):
        """加载 Hash 列表"""
        hash2path = {}
        path2hash = {}
        if self.hashfile.exists():
            for line in self.hashfile.open():
                line = line.strip()
                if not line:
                    continue
                md5, path = line.strip().split(maxsplit=1)
                assert md5 not in hash2path
                hash2path[md5] = path
                path2hash[path] = md5

            self.hash2path = hash2path
            self.path2hash = path2hash

        if RunMode.verbose:
            print("Load %d hash from %s" % (len(hash2path), self.hashfile))
        return hash2path, path2hash

    def _hash_save(self):
        """Save hash"""
        if not self.dirty or RunMode.test:
            return True

        tmpfile = str(self.hashfile) + ".tmp"
        with open(tmpfile, 'w') as fp_:
            for path, md5 in self.path2hash.items():
                fp_.write("%s %s\n" % (md5, path))

        os.rename(tmpfile, self.hashfile)
        self.dirty = False
        return True

    def _hash_del_file(self, path):
        """从Hash数据库里删除一个目录下文件"""
        assert str(path) in self.path2hash
        md5 = self.path2hash.pop(path)
        del self.hash2path[md5]
        self.dirty = True
        return True

    def _hash_add_file(self, path):
        """向Hash数据库里添加一个目录下文件"""
        assert str(path) not in self.path2hash
        fullpath = self.home / path
        md5 = hashlib.md5(fullpath.read_bytes()).hexdigest()
        self.path2hash[path] = md5
        self.hash2path[md5] = path
        self.dirty = True
        return True

    def _hash_move_file(self, opath, npath):
        """移动 HashDB 里的文件"""
        assert str(opath) in self.path2hash
        assert str(npath) not in self.path2hash
        md5 = self.path2hash.pop(opath)
        assert md5 in self.hash2path
        self.path2hash[npath] = md5
        self.hash2path[md5] = npath
        self.dirty = True
        return True

    def _list_dir(self):
        """列出目录下所有文件"""
        files = []
        cwd = Path.cwd()
        os.chdir(self.home)
        for root, _, names in os.walk('.'):
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
        """根据 datetime 对象得到对应的文件路径"""
        subdir = dt_.date().strftime("%Y/%m/%d")
        name = dt_.time().strftime("%H%M%S")

        apath = self.home / subdir
        for i in range(self.MAX_NO):
            dst = apath / ("%s%02d%s" % (name, i, suffix))
            if not dst.exists():
                return dst
        return None

    def _path2dt(self, path):
        rpath = Path(path).relative_to(self.home).with_suffix("")
        return datetime.strptime(str(rpath)[:-2], "%Y/%m/%d/%H%M%S")

    def exists(self, md5):
        """一个Hash是否存在"""
        return md5 in self.hash2path

    def add_file(self, src, dt_, md5):
        """Add a file"""
        if md5 in self.hash2path:
            if RunMode.verbose:
                print("ADD: ignore dupe file [%s]" % src)
            return 'dupe'

        dst = self._dt2path(dt_, src.suffix.lower())
        if not dst:
            print(f"E: add_file({src}, {dt_})")
            return 'err'

        if RunMode.verbose:
            print(f"ADD {src} to {dst}")

        if RunMode.test:
            return None

        dst.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        path = dst.relative_to(self.home)
        self.hash2path[md5] = str(path)
        self.path2hash[str(path)] = md5
        self.dirty = True
        return None

    def move_file(self, path, dt_):
        """Move file to new locaton according dt_"""
        newpath = self._dt2path(dt_, path.suffix)
        if not newpath:
            print(f"E: move_file({path}, {dt_}")
            return None

        if newpath.parent == path.parent and newpath.stem[:-2] == path.stem[:-2]:
            return False

        new_rpath = str(newpath.relative_to(self.home))
        old_rpath = str(path.relative_to(self.home))
        if RunMode.verbose:
            print(f"Moving {old_rpath} to {new_rpath}")

        self._hash_move_file(old_rpath, new_rpath)

        if not RunMode.test:
            path.rename(newpath)
        return True

    def stat_suffix(self):
        """统计文件扩展名"""
        counts = Counter()
        for path in self.path2hash:
            suffix = path.rsplit('.', 1)[1]
            counts[suffix] += 1
        return counts

    def sync(self):
        """同步Hash文件和目录"""
        paths = set(self._list_dir())
        files = set(self.path2hash.keys())

        removed = files - paths
        if removed:
            for path in removed:
                if RunMode.verbose:
                    print(f"File {path} has been removed")
                self._hash_del_file(path)

        added = paths - files
        if added:
            for path in added:
                if RunMode.verbose:
                    print(f"Add file {path} to HashDB")
                self._hash_add_file(path)

        if any([added, removed]):
            self._hash_save()
        return len(removed), len(added)

    def __del__(self):
        """对象销毁时自动保存"""
        self._hash_save()
