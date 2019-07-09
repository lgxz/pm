#!/usr/bin/env python
# coding: utf-8

"""照片时间判断"""

from pathlib import Path
from datetime import datetime
from datetime import timezone

from pm import RunMode


class PhotoTime(dict):
    """处理照片时间

    mtime: 文件的 st_mtime，带时区，但是为当前电脑的时区
    create: 拍照设备拍照时生成，不带时区，为拍照设备当时设置的时区，无法知道当时的时区
    orig: 同上
    creation: 视频文件才有，带拍照设备当时设置的时区
    gps: 来自 GPS 的时间，时区为UTC
    """

    tag_names = ['mtime', 'create', 'orig', 'creation', 'gps']
    tag_formats = ['%Y:%m:%d %H:%M:%S%z', '%Y:%m:%d %H:%M:%S', '%Y:%m:%d %H:%M:%S', '%Y:%m:%d %H:%M:%S%z', '']

    def __init__(self, path, dts):
        """Init"""
        assert len(dts) <= len(self.tag_names)
        dict.__init__(self)
        self.path = Path(path)
        gps_dts = None
        for i, dt_ in enumerate(dts):
            if not dt_:
                continue
            if dt_.startswith('00') or dt_.startswith('19'):
                print(f"W: [{path}] -> ignore time {dt_}")
                continue

            tag = self.tag_names[i]
            if tag != 'gps':
                try:
                    dto = datetime.strptime(dt_, self.tag_formats[i])
                except ValueError:
                    print("W: [%s] -> ignore invalid [%s] time [%s]" % (path, tag, dt_))
                    continue
                self[tag] = dto
            else:
                gps_dts = dt_

        if gps_dts:
            gps_dt = None
            for tag_format in ('%Y:%m:%d %H:%M:%S.%fZ', '%Y:%m:%d %H:%M:%SZ'):
                try:
                    gps_dt = datetime.strptime(gps_dts, tag_format)
                except ValueError:
                    pass

            if gps_dt:
                self['gps'] = gps_dt.astimezone(timezone.utc)
            else:
                print("W: [%s] -> ignore invalid [GPS] time [%s]" % (path, gps_dts))

    def get_datetime(self):
        """判断拍照时间"""
        # 视频文件的 CreationDate 是准确的
        suffix = self.path.suffix.lower()
        if 'creation' in self:
            if suffix in ('.mov', '.m4v', '.mp4'):
                return self['creation']

            if RunMode.verbose:
                print(f"I: {self.path} has creation date")

        # GPS 时间准确，用 GPS 时间做基准去掉严重偏离的时间
        if 'gps' in self:
            gps_date = self['gps'].date()
            for tag in list(self.keys()):
                dt_ = self[tag]
                delta = dt_.date() - gps_date
                if abs(delta.days) > 1:
                    if RunMode.verbose:
                        print("W: [%s](%s) >>> [%s](GPS)" % (dt_, tag, self['gps']))
                    del self[tag]

            # 过滤后剩余的时间差异不大，按下述优先顺序选择一个
            for tag in ('create', 'orig', 'creation', 'mtime', 'gps'):
                if tag in self:
                    return self[tag]

        # 如果 create 和 orig 相等，认为是拍照时间
        try:
            if self['create'] == self['orig']:
                return self['create']
        except KeyError:
            pass

        # 选择最小的日期
        return sorted(self.values(), key=lambda dt_: dt_.timestamp())[0]

    def __str__(self):
        """Str"""
        return "%s: %s" % (self.path, ' '.join(["%s=%s" % (tag, dt_.isoformat()) for tag, dt_ in self.items()]))