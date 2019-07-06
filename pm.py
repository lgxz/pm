#!/usr/bin/env python
# coding: utf-8

import os
import shutil
import hashlib
from pathlib import Path
from collections import Counter


m_test = False
m_verbose = False


class DirHash():
    HASH_FILE = ".hash"

    def __init__(self, home):
        self.home = Path(home)
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
                assert(md5 not in hash2path)
                hash2path[md5] = path
                path2hash[path] = md5

            self.hash2path = hash2path
            self.path2hash = path2hash

        if m_verbose: print("Load %d hash from %s" % (len(hash2path), self.hashfile))
        return hash2path, path2hash


    def _hash_save(self):
        """Save hash"""
        if not self.dirty or m_test:
            return True

        tmpfile = str(self.hashfile) + ".tmp"
        with open(tmpfile, 'w') as fp:
            for path, md5 in self.path2hash.items():
                fp.write("%s %s\n" % (md5, path))

        os.rename(tmpfile, self.hashfile)
        self.dirty = False
        return True


    def _hash_del_file(self, path):
        """从Hash数据库里删除一个目录下文件"""
        assert(str(path) in self.path2hash)
        md = self.path2hash.pop(path)
        del self.hash2path[md]
        self.dirty = True
        return True


    def _hash_add_file(self, path):
        """向Hash数据库里添加一个目录下文件"""
        assert(str(path) not in self.path2hash)
        p = self.home / path
        md5 = hashlib.md5(p.read_bytes()).hexdigest()
        self.path2hash[path] = md5
        self.hash2path[md5] = path
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
                    except:
                        pass
                if not name.startswith('.'):
                    files.append(path[2:])

        os.chdir(cwd)
        return files


    def exists(self, md):
        """一个Hash是否存在"""
        return md in self.hash2path


    def add_file(self, src, subdir, name, md):
        """Add a file"""
        if md in self.hash2path:
            if m_verbose: print("ADD: ignore dupe file [%s]" % src)
            return 'dupe'

        d = self.home / subdir 
        d.mkdir(mode=0o700, parents=True, exist_ok=True)
        suffix = src.suffix.lower()
        for i in range(100):
            t = d / ("%s%02d%s" % (name, i, suffix))
            if not t.exists():
                break

        if i == 100:
            print("ERR: to many filename collision")
            return 'err'

        if m_test: return None

        shutil.copy2(src, t)
        path = t.relative_to(self.home)
        self.hash2path[md] = str(path)
        self.path2hash[str(path)] = md
        self.dirty = True
        return None

 
    def stat_suffix(self):
        """统计文件扩展名"""
        cs = Counter()
        for path in self.path2hash.keys():
            suffix = path.rsplit('.', 1)[1]
            cs[suffix] += 1
        return cs

       
    def sync(self):
        """同步Hash文件和目录"""
        paths = set(self._list_dir())
        files = set(self.path2hash.keys())

        removed = files - paths
        if removed:
            for path in removed:
                if m_verbose: print(f"File {path} has been removed")
                self._hash_del_file(path)

        added = paths - files
        if added:
            for path in added:
                if m_verbose: print(f"Add file {path} to HashDB")
                self._hash_add_file(path)

        if any([added, removed]):
            self._hash_save()
        return len(removed), len(added)


    def __del__(self):
        self._hash_save()


class PhotoHome(DirHash):
    pass


def get_datetime(path, dts):
    """判断拍照时间"""
    #GPS DateTime: 2015:04:01 02:55:15Z / 2015:04:11 09:10:42.65Z
    if dts[-1]:
        #UTC Time, 暂不转换为本地时间
        dts[-1] = dts[-1].split('.')[0].replace('Z', '')

    #删除时区
    for i in range(len(dts) - 1):
        if not dts[i]:
            continue

        pos = dts[i].rfind('+')
        if pos > 0:
            dts[i] = dts[i][:pos]

    values = list(filter(None, dts))
    days = {s.split()[0] for s in values}
    if len(days) > 1:
        print(f"W: {path} <> {dts}")

    if len(dts) > 3 and dts[3] and path.suffix in ('.mov', '.mp4'):
        s = dts[3]
    else:
        s = min(values)

    if m_verbose:
        print(f"{path} -> {s}")

    date, hms = s.split()
    date = date.replace(':', '/')
    hms = hms.replace(':', '')
    return date, hms


def do_import(home, datefile, srcdir):
    """执行导入"""
    cs = Counter()
    for line in datefile.open():
        line = line.strip()
        if not line:
            continue

        path, md, *dts = line.rsplit(',')
        if home.exists(md):
            if m_verbose: print("Import: ignore dupe file %s" % path)
            continue

        if srcdir:
            p = srcdir / path
        else:
            p = Path(path)

        day, hms = get_datetime(p, dts)
        err = home.add_file(p, day, hms, md)
        if not err:
            cs['ok'] += 1
        else:
            cs[err] += 1

    return cs


def cmd_import(home, args):
    """处理照片导入命令"""
    datefile = Path(args.files[0])
    if len(args.files) == 1:
        srcdir = None
    else:
        srcdir = Path(args.files[1])

    ret = do_import(home, datefile, srcdir)
    print(ret)


def cmd_sync(home, _):
    """目录同步命令"""
    removed, added = home.sync()
    print(f"Remove {removed} files from HashDB")
    print(f"Add {added} files to HashDB")


def cmd_stat(home, _):
    """状态统计"""
    stats = home.stat_suffix()
    for suffix, count in stats.most_common():
        print(f"{suffix}: {count}")
    print("Total %d files" % sum(stats.values()))


def main(args):
    """Main function"""
    global m_test, m_verbose

    m_test = args.test
    m_verbose = args.verbose
    home = PhotoHome(args.home)
    args.func(home, args)


if __name__ == '__main__':
    def parse_cmdline():
        """ cmd parse """
        import argparse

        parser = argparse.ArgumentParser(description="Template Python App")
        parser.add_argument('--home', default='/Volumes/RED/home', help='Photo home')
        parser.add_argument('--test', action="store_true", help='Dryrun mode')
        parser.add_argument('--verbose', action="store_true", help='Verbose mode')
        subparsers = parser.add_subparsers(dest='cmd', required=True, help='sub-command help')

        sp_import = subparsers.add_parser('import', help='Import photos')
        sp_import.add_argument('files', type=str, nargs='+', help='Input files')
        sp_import.set_defaults(func=cmd_import)

        sp_sync = subparsers.add_parser('sync', help='Sync photos and meta file')
        sp_sync.set_defaults(func=cmd_sync)

        sp_stat = subparsers.add_parser('stat', help='Photo stats')
        sp_stat.set_defaults(func=cmd_stat)

        args = parser.parse_args()
        return args

    main(parse_cmdline())

