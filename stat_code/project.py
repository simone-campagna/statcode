#!/usr/bin/env python3

import os
import fnmatch
import collections

from .code_file import File, FileStats

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

    def report(self, print_function=print):
        tot_files = 0
        tot_stats = FileStats()
        languages = sorted(self._language_files.keys())
        fmt_header = "{:16} {:>12s} {:>12s} {:>12s}"
        fmt_data = "{:16} {:12d}"
        fmt_code = fmt_data + " {:12d} {:12d}"
        print_function(fmt_header.format('LANGUAGE', '#FILES', '#LINES', '#BYTES'))
        for language in languages:
            code_files = self._language_files[language]
            #if language == File.UNCLASSIFIED:
            #    for code_file in code_files:
            #        print_function("   ", language, code_file.filepath)
            if language == File.DATA:
                print_function(fmt_data.format(language, len(code_files)))
                continue
            language_stats = FileStats()
            for code_file in code_files:
                language_stats += code_file.stats
            tot_files += len(code_files)
            tot_stats += language_stats
            print_function(fmt_code.format(language, len(code_files), language_stats.num_lines, language_stats.num_bytes))
        print_function()
        print_function(fmt_code.format('TOTAL', tot_files, tot_stats.num_lines, tot_stats.num_bytes))

