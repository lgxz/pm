#!/usr/bin/env python
# coding: utf-8

"""处理 sync 命令"""

from pathlib import Path
from collections import Counter

from pm.photo import PhotoTime


def cmd_sync(home, args):
    """目录同步命令"""
    if not args.file:
        removed, added = home.sync()
        print(f"W: {added} unknown files")
        print(f"Remove {removed} files from HashDB")
        return

    counts = Counter()
    for line in open(args.file, 'r'):
        line = line.strip()
        if not line:
            continue

        path, *dts = line.rsplit(',')
        path = Path(path)
        pt_ = PhotoTime(path, dts)
        dt_ = pt_.get_datetime()

        err = home.move_file(path, dt_)
        if not err:
            counts['ok'] += 1
        else:
            counts[err] += 1

    print(counts)


def init(sp_):
    """Init"""
    sp_sync = sp_.add_parser('sync', help='Sync photos and meta file')
    sp_sync.add_argument('file', type=str, nargs='?', help='Input file')
    sp_sync.set_defaults(func=cmd_sync)
