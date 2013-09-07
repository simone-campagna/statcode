#!/usr/bin/env python3

class FileStats(object):
    files = 1
    dirs = 0
    def __init__(self, lines=0, bytes=0):
        self.lines = lines
        self.bytes = bytes

    def __add__(self, stats):
        return self.__class__(self.lines + stats.lines, self.bytes + stats.bytes)

    def __iadd__(self, stats):
        self.lines += stats.lines
        self.bytes += stats.bytes
        return self

    def clear(self):
        self.lines = 0
        self.bytes = 0

    def __repr__(self):
        return "{}(lines={}, bytes={})".format(self.__class__.__name__, self.lines, self.bytes)
    __str__ = __repr__

class DirStats(FileStats):
    def __init__(self, files=0, lines=0, bytes=0):
        self.files = files
        super().__init__(lines, bytes)

    def __add__(self, stats):
        return self.__class__(self.files + stats.files, self.lines + stats.lines, self.bytes + stats.bytes)

    def __iadd__(self, stats):
        self.files += stats.files
        self.lines += stats.lines
        self.bytes += stats.bytes
        return self

    def clear(self):
        self.files = 0
        super().clear()

    def __repr__(self):
        return "{}(files={}, lines={}, bytes={})".format(self.__class__.__name__, self.files, self.lines, self.bytes)
    __str__ = __repr__

class TreeStats(DirStats):
    def __init__(self, dirs=0, files=0, lines=0, bytes=0):
        self.dirs  = dirs
        super().__init__(files, lines, bytes)

    def __add__(self, stats):
        return self.__class__(self.dirs + stats.dirs, self.files + stats.files, self.lines + stats.lines, self.bytes + stats.bytes)

    def __iadd__(self, stats):
        self.dirs  += stats.dirs
        self.files += stats.files
        self.lines += stats.lines
        self.bytes += stats.bytes
        return self

    def clear(self):
        self.dirs = 0
        super().clear()

    def __repr__(self):
        return "{}(dirs={}, files={}, lines={}, bytes={})".format(self.__class__.__name__, self.dirs, self.files, self.lines, self.bytes)
    __str__ = __repr__

