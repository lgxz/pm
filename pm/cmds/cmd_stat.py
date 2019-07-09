#!/usr/bin/env python
# coding: utf-8

"""处理 stat 命令"""


def cmd_stat(home, _):
    """状态统计"""
    stats = home.stat_suffix()
    for suffix, count in stats.most_common():
        print(f"{suffix}: {count}")
    print("Total %d files" % sum(stats.values()))


def init(sp_):
    """Init"""
    sp_stat = sp_.add_parser('stat', help='Photo stats')
    sp_stat.set_defaults(func=cmd_stat)
