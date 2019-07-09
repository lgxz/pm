#!/usr/bin/env python
# coding: utf-8

"""处理照片导入命令"""

from pathlib import Path
from collections import Counter

from pm.photo import PhotoTime


def do_import(home, datefile):
    """执行导入"""
    counts = Counter()
    for line in datefile.open():
        line = line.strip()
        if not line:
            continue

        path, *dts = line.rsplit(',')
        path = Path(path)
        pt_ = PhotoTime(path, dts)
        dt_ = pt_.get_datetime()

        err = home.add_file(path, dt_)
        if not err:
            counts['ok'] += 1
        else:
            print(f'E: {err} -> [{path}]')
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
