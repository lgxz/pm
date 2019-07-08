#!/usr/bin/env python
# coding: utf-8

"""Init cmds"""

from pathlib import Path
from importlib import import_module

PKG = "pm.cmds"


def init(sp_):
    """Init"""
    curdir = Path(__file__).parent
    paths = curdir.glob('cmd_*.py')
    for path in paths:
        filename = path.stem
        mod = import_module(f".{filename}", package=PKG)
        mod.init(sp_)
