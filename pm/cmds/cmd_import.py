#!/usr/bin/env python
# coding: utf-8

"""处理照片导入命令"""

from pathlib import Path
from collections import Counter

from pm import RunMode
from pm.photo import PhotoTime


def do_import(home, datefile):
    """执行导入"""
    counts = Counter()
    for line in datefile.open():
        line = line.strip()
        if not line:
            continue

        path, md5, *dts = line.rsplit(',')
        if home.exists(md5):
            if RunMode.verbose:
                print("Import: ignore dupe file %s" % path)
            continue

        path = Path(path)
        pt_ = PhotoTime(path, dts)
        dt_ = pt_.get_datetime()

        err = home.add_file(path, dt_, md5)
        if not err:
            counts['ok'] += 1
        else:
            counts[err] += 1

    return counts


def cmd_import(home, args):
    """处理照片导入命令"""
    datefile = Path(args.file)
    ret = do_import(home, datefile)
    print(ret)


def init(sp_):
    """Init"""
    sp_import = sp_.add_parser('import', help='Import photos')
    sp_import.add_argument('file', type=str, help='Input files')
    sp_import.set_defaults(func=cmd_import)
