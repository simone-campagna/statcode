#!/usr/bin/env python3

import os
import fnmatch
import collections

from .code_file import File, FileStats

ProjectEntry = collections.namedtuple('ProjectEntry', ('language', 'files', 'lines', 'bytes'))
FileEntry = collections.namedtuple('FileEntry', ('language', 'lines', 'bytes', 'filepath'))

class SortKey(object):
    REVERSE = {'+': False, '-': True}
    FIELDS = ProjectEntry._fields + tuple(filter(lambda f: not f in ProjectEntry._fields, FileEntry._fields))
    def __init__(self, s):
        self.key = None
        self.reverse = False
        if s in self.FIELDS:
            self.key = s
        if s:
            if s[0] in '+-' and s[1:] in self.FIELDS:
                self.key = s[1:]
                self.reverse = self.REVERSE[s[0]]
        if self.key is None:
            raise ValueError("invalid sort_key {!r}; valid values are {}".format(s, self.choices()))

    @classmethod
    def choices(cls):
        return '|'.join("[+-]{}".format(k) for k in cls.FIELDS)

class Project(object):
    EXCLUDE_DIRS = {'.git', '.svn', 'CVS'}
    EXCLUDE_FILES = {'.*.swp', '*.pyc', '.gitignore', '.svnignore'}
    def __init__(self, project_dir, language_hints=None, exclude_dirs=None, exclude_files=None):
        self.project_dir = project_dir
        if language_hints is None:
            language_hints = ()
        if exclude_dirs is None:
            exclude_dirs = self.EXCLUDE_DIRS
        self.exclude_dirs = exclude_dirs
        if exclude_files is None:
            exclude_files = self.EXCLUDE_FILES
        self.exclude_files = exclude_files
        assert isinstance(language_hints, collections.Sequence)
        self._language_hints = language_hints
        self._language_files = collections.defaultdict(list)
        self._directories = {}
        self.classify()

    def classify(self):
        unclassified_files = []
        for dirpath, dirnames, filenames in os.walk(self.project_dir, topdown=True):
            excluded_dirnames = set()
            for dir_pattern in self.exclude_dirs:
                excluded_dirnames.update(fnmatch.filter(dirnames, dir_pattern))
            if excluded_dirnames:
                filtered_dirnames = list(filter(lambda dirname: not dirname in excluded_dirnames, dirnames))
                del dirnames[:]
                dirnames.extend(filtered_dirnames)
            excluded_filenames = set()
            for file_pattern in self.exclude_files:
                excluded_filenames.update(fnmatch.filter(filenames, file_pattern))
            if excluded_filenames:
                filenames = list(filter(lambda filename: not filename in excluded_filenames, filenames))
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                code_file = File(self, filepath)
                if code_file.language:
                    self._language_files[code_file.language].append(code_file)
                else:
                    unclassified_files.append(code_file)
        for code_file in unclassified_files:
            code_file.post_classify()
            self._language_files[code_file.language].append(code_file)

    def most_common_languages(self):
        for language, files in sorted(((language, files) for language, files in self._language_files.items()), key=lambda x: -len(x[1])):
            yield language
        
    def language_hints(self):
        return iter(self._language_hints)

    def report(self, print_function=print, sort_keys=None):
        tot_files = 0
        tot_stats = FileStats()
        languages = sorted(self._language_files.keys(), key=lambda x: x.lower())
        fmt_header = "{:16} {:>12s} {:>12s} {:>12s}"
        fmt_data = "{:16} {:12d}"
        fmt_code = fmt_data + " {:12d} {:12d}"
        print_function(fmt_header.format('LANGUAGE', '#FILES', '#LINES', '#BYTES'))
        table = []
        for language, code_files in self._language_files.items():
            language_stats = FileStats()
            if language != File.DATA:
                for code_file in code_files:
                    language_stats += code_file.stats
            table.append(ProjectEntry(
                language=language,
                files=len(code_files),
                lines=language_stats.num_lines,
                bytes=language_stats.num_bytes))

        table.sort(key=lambda x: x.language)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in ProjectEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            if entry.language == File.DATA:
                fmt = fmt_data
            else:
                fmt = fmt_code
            print_function(fmt.format(entry.language, entry.files, entry.lines, entry.bytes))
        print_function()
        print_function(fmt_code.format('TOTAL', tot_files, tot_stats.num_lines, tot_stats.num_bytes))

    def list_language_files(self, language, print_function=print, sort_keys=None):
        if language in self._language_files:
            fmt_header = "{:16} {:>12s} {:>12s} {}"
            fmt_data = "{:16}"
            fmt_code = fmt_data + " {:12d} {:12d} {}"
            print_function(fmt_header.format('LANGUAGE', '#LINES', '#BYTES', 'FILENAME'))
            table = []
            tot_stats = FileStats()
            for code_file in self._language_files[language]:
                stats = code_file.stats
                tot_stats += stats
                table.append(FileEntry(language=language, lines=stats.num_lines, bytes=stats.num_bytes, filepath=code_file.filepath))

        table.sort(key=lambda x: x.language)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in FileEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            if entry.language == File.DATA:
                fmt = fmt_data
            else:
                fmt = fmt_code
            print_function(fmt.format(entry.language, entry.lines, entry.bytes, entry.filepath))
        print_function()
        print_function(fmt_code.format('TOTAL', tot_stats.num_lines, tot_stats.num_bytes, ''))
