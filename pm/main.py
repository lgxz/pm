#!/usr/bin/env python
# coding: utf-8

"""主程序"""

import argparse
from pathlib import Path

from pm import RunMode
from pm import cmds
from pm.photo import PhotoHome


def main():
    """Main"""
    args = parse_cmdline()

    RunMode.test = args.test
    RunMode.verbose = args.verbose
    home = Path(args.home).expanduser().resolve(True)
    args.func(PhotoHome(home), args)


def parse_cmdline():
    """Parse cmdline"""
    parser = argparse.ArgumentParser(description="Stupid Photo Manager")
    parser.add_argument('--home', default='~/.photos', help='Photo home')
    parser.add_argument('--test', action="store_true", help='Dryrun mode')
    parser.add_argument('--verbose', action="store_true", help='Verbose mode')
    subparsers = parser.add_subparsers(dest='cmd', required=True, help='sub-command help')
    cmds.init(subparsers)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
