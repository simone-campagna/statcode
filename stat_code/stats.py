#!/usr/bin/env python3

class Stats(object):
    def __init__(self, num_files=0, num_lines=0, num_bytes=0):
        self.num_files = num_files
        self.num_lines = num_lines
        self.num_bytes = num_bytes

    def __add__(self, stats):
        return self.__class__(self.num_files + stats.num_files, self.num_lines + stats.num_lines, self.num_bytes + stats.num_bytes)

    def __iadd(self, stats):
        self.num_files += stats.num_files
        self.num_lines += stats.num_lines
        self.num_bytes += stats.num_bytes

