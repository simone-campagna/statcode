#!/usr/bin/env python3
#
# Copyright 2013 Simone Campagna
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

__author__ = 'Simone Campagna'

class FileStats(object):
    __fields__ = ('lines', 'bytes')
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

    def tostr(self):
        return ', '.join("{}={!r}".format(field, getattr(self, field)) for field in self.__fields__)

    def result(self):
        return ', '.join("{!r} {}".format(getattr(self, field), field) for field in self.__fields__)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.tostr())

    def __str__(self):
        return repr(self)

class DirStats(FileStats):
    __fields__ = ('files', 'lines', 'bytes')
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

#    def __repr__(self):
#        return "{}(files={}, lines={}, bytes={})".format(self.__class__.__name__, self.files, self.lines, self.bytes)
#    __str__ = __repr__

class TreeStats(DirStats):
    __fields__ = ('dirs', 'files', 'lines', 'bytes')
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

#    def __repr__(self):
#        return "{}(dirs={}, files={}, lines={}, bytes={})".format(self.__class__.__name__, self.dirs, self.files, self.lines, self.bytes)
#    __str__ = __repr__

