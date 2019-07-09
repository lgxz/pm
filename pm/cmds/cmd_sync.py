#!/usr/bin/env python
# coding: utf-8

"""处理 sync 命令"""

from pathlib import Path

from pm.photo import PhotoTime


def cmd_sync(home, args):
    """目录同步命令"""
    if not args.file:
        removed, added = home.sync()
        print(f"Remove {removed} files from HashDB")
        print(f"Add {added} files to HashDB")
        return

    count = 0
    for line in open(args.file, 'r'):
        line = line.strip()
        if not line:
            continue

        path, *dts = line.rsplit(',')
        path = Path(path)
        pt_ = PhotoTime(path, dts)
        dt_ = pt_.get_datetime()
        if home.move_file(path, dt_):
            count += 1
    print(f"{count} files relocated")


def init(sp_):
    """Init"""
    sp_sync = sp_.add_parser('sync', help='Sync photos and meta file')
    sp_sync.add_argument('file', type=str, nargs='?', help='Input file')
    sp_sync.set_defaults(func=cmd_sync)
