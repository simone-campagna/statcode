#!/usr/bin/env python3

class FileStats(object):
    files = 1
    dirs = 0
    def __init__(self, lines=0, bytes=0):
        self.lines = lines
        self.bytes = bytes

    def __add__(self, stats):
        return self.__class__(self.lines + stats.lines, self.bytes + stats.bytes)

    def __iadd(self, stats):
        self.lines += stats.lines
        self.bytes += stats.bytes

class DirStats(FileStats):
    def __init__(self, dirs=0, files=0, lines=0, bytes=0):
        self.dirs  = dirs
        self.files = files
        super().__init__(lines, bytes)

    def __add__(self, stats):
        return self.__class__(self.dirs + stats.dirs, self.files + stats.files, self.lines + stats.lines, self.bytes + stats.bytes)

    def __iadd(self, stats):
        self.dirs  += stats.dirs
        self.files += stats.files
        self.lines += stats.lines
        self.bytes += stats.bytes
