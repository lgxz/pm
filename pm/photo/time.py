#!/usr/bin/env python
# coding: utf-8

"""照片时间判断."""

from pathlib import Path
from datetime import datetime
from datetime import timezone

from pm import RunMode


FORMATS_UTC = ('%Y:%m:%d %H:%M:%S.%fZ', '%Y:%m:%d %H:%M:%SZ')
FORMATS_OTHERS = ('%Y:%m:%d %H:%M:%S', '%Y:%m:%d %H:%M:%S%z', '%Y:%m:%d %H:%M%z')


def parse_datetime(dts):
    """Parse datetime string."""
    if dts[-1] == 'Z':
        formats = FORMATS_UTC
        utc = True
    else:
        formats = FORMATS_OTHERS
        utc = False

    dto = None
    for fmt in formats:
        try:
            dto = datetime.strptime(dts, fmt)
            break
        except ValueError:
            pass

    if dto and utc:
        dto = dto.astimezone(timezone.utc)
    return dto


class PhotoTime(dict):
    """处理照片时间.

    mtime: 文件的 st_mtime，带时区，但是为当前电脑的时区
    create: 拍照设备拍照时生成，不带时区，为拍照设备当时设置的时区，无法知道当时的时区
    orig: 同上
    creation: 视频文件才有，带拍照设备当时设置的时区
    gps: 来自 GPS 的时间，时区为UTC
    """

    tag_names = ['mtime', 'create', 'orig', 'creation', 'gps']

    def __init__(self, path, dts):
        """Init."""
        assert len(dts) <= len(self.tag_names)
        dict.__init__(self)
        self.path = Path(path)

        today = datetime.today().date()
        for i, dt_ in enumerate(dts):
            dt_ = dt_.strip()
            if not dt_:
                continue

            tag = self.tag_names[i]

            dto = parse_datetime(dt_)
            if not dto:
                print("W: [%s] -> ignore invalid [%s] time [%s]" % (path, tag, dt_))
                continue

            if dto.year < 2000 or dto.date() > today:
                print(f"W: [{path}] -> ignore time {dt_}")
                continue

            self[tag] = dto

    def get_datetime(self):
        """判断拍照时间."""
        # 视频文件的 CreationDate 是准确的
        suffix = self.path.suffix.lower()
        if 'creation' in self:
            if suffix in ('.mov', '.m4v', '.mp4'):
                return self['creation']

            if RunMode.verbose:
                print(f"I: {self.path} has creation date")

        items = [(tag, dto, int(dto.timestamp())) for tag, dto in self.items()]
        if len(items) == 1:
            # 没有选择 :(
            return items[0][1]

        # 如果 create 和 orig 相等，认为是拍照时间
        try:
            if self['create'] == self['orig']:
                return self['create']
        except KeyError:
            pass

        # 把相差一天内的日期分组
        items.sort(key=lambda item: item[2])
        groups = [[items[0]]]
        for item in items[1:]:
            if item[-1] - groups[-1][-1][-1] <= 86400:
                groups[-1].append(item)
            else:
                groups.append([item])

        groups.sort(key=len, reverse=True)
        group = groups[0]
        if len(group) == 1:
            return group[0][1]

        # 如果第一个元素是 gps，返回第二个
        if group[0][0] == 'gps':
            return group[1][1]
        return group[0][1]

    def __str__(self):
        """Str."""
        return "%s: %s" % (self.path, ' '.join(["%s=%s" % (tag, dt_.isoformat()) for tag, dt_ in self.items()]))
