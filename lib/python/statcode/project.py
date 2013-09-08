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

import os
import abc
import fnmatch
import collections

from .stats import FileStats, DirStats, TreeStats
from .language import LanguageClassifier
from .statcode_config import StatCodeConfig
from .project_file import ProjectFile
from .project_dir import ProjectDir
from .project_tree import ProjectTree, BaseTree

DirEntry = collections.namedtuple('DirEntry', ('language', 'files', 'lines', 'bytes'))
FileEntry = collections.namedtuple('FileEntry', ('language', 'lines', 'bytes', 'filepath'))
ProjectEntry = collections.namedtuple('ProjectEntry', ('projects', 'files', 'lines', 'bytes'))

_FIELDS = DirEntry._fields 
_FIELDS += tuple(filter(lambda f: not f in _FIELDS, FileEntry._fields))
_FIELDS += tuple(filter(lambda f: not f in _FIELDS, ProjectEntry._fields))

class SortKey(object):
    FIELDS = _FIELDS
    REVERSE = {'+': False, '-': True}
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

class BaseProject(BaseTree, metaclass=abc.ABCMeta):
    def __init__(self, name):
        self.name = name
        #self.language_project_files = collections.defaultdict(list)
        #self.language_dir_stats = collections.defaultdict(DirStats)
        #self.tot_stats = DirStats()
        super().__init__()

    def project_entry(self):
        return ProjectEntry(projects=self.num_projects(), files=self.tree_stats.files, lines=self.tree_stats.lines, bytes=self.tree_stats.bytes)

    @abc.abstractmethod
    def num_projects(self):
        pass

    def merge_project(self, project):
        assert isinstance(project, BaseProject)
        super().merge_tree(project)


    def report(self, *, print_function=print, sort_keys=None, patterns=None, pattern_type='+'):
        if self.name:
            print("=== Project[{}]".format(self.name))
        if patterns is None:
            patterns = []
        if pattern_type is None:
            pattern_type = '+'
        languages = sorted(self.tree_language_project_files.keys(), key=lambda x: x.lower())
        fmt_header = "{language:16} {files:>12s} {lines:>12s} {bytes:>12s}"
        fmt_data = "{language:16} {files:12d} {lines:12d} {bytes:12d}"
        fmt_code = "{language:16} {files:12d} {lines:12d} {bytes:12d}"
        print_function(fmt_header.format(language='LANGUAGE', files='#FILES', lines='#LINES', bytes='#BYTES', null=''))
        table = []
        tree_stats = TreeStats()
        languages = set(self.tree_language_stats.keys())
        if pattern_type == '-':
            for pattern in patterns:
                languages.difference_update(fnmatch.filter(languages, pattern))
        else:
            selected_languages = set()
            for pattern in patterns:
                selected_languages.update(fnmatch.filter(languages, pattern))
            languages = selected_languages
        for language in languages:
            language_stats = self.tree_language_stats[language]
            table.append(DirEntry(
                language=language,
                files=language_stats.files,
                lines=language_stats.lines,
                bytes=language_stats.bytes))
            tree_stats += language_stats

        table.sort(key=lambda x: x.language)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in DirEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            if LanguageClassifier.language_has_lines_stats(entry.language):
                fmt = fmt_code
            else:
                fmt = fmt_data
            print_function(fmt.format(language=entry.language, files=entry.files, lines=entry.lines, bytes=entry.bytes, null=''))
        print_function(fmt_code.format(language='TOTAL', files=tree_stats.files, lines=tree_stats.lines, bytes=tree_stats.bytes, null=''))
        print_function()

    def list_language_files(self, language_pattern, *, print_function=print, sort_keys=None):
        languages = []
        for language in self.tree_language_project_files:
            if fnmatch.fnmatch(language, language_pattern):
                languages.append(language)
        self.list_languages_files(languages, print_function=print_function, sort_keys=sort_keys)

    def list_languages_files(self, languages, *, print_function=print, sort_keys=None):
        if self.name:
            print("=== Project[{}]".format(self.name))

        fmt_header = "{language:16s} {lines:>12s} {bytes:>12s} {file}"
        fmt_data = "{language:16s} {lines:12d} {bytes:12d} {file}"
        fmt_code = "{language:16s} {lines:12d} {bytes:12d} {file}"
        print_function(fmt_header.format(language='LANGUAGE', lines='#LINES', bytes='#BYTES', file='FILENAME', null=''))
        table = []
        tree_stats = TreeStats()
        for language in languages:
            if not language in self.tree_language_project_files:
                continue
            for project_file in self.tree_language_project_files[language]:
                stats = project_file.stats
                tree_stats += stats
                table.append(FileEntry(language=language, lines=stats.lines, bytes=stats.bytes, filepath=project_file.filepath))
    
        table.sort(key=lambda x: x.language)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in FileEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            if LanguageClassifier.language_has_lines_stats(entry.language):
                fmt = fmt_code
            else:
                fmt = fmt_data
            print_function(fmt.format(language=entry.language, lines=entry.lines, bytes=entry.bytes, file=entry.filepath, null=''))
        print_function(fmt_code.format(language='TOTAL', lines=tree_stats.lines, bytes=tree_stats.bytes, file='', null=''))
        print_function()


class Project(BaseProject):
    EXCLUDE_DIRS = {'.git', '.svn', 'CVS', '__pycache__'}
    EXCLUDE_FILES = {'.*.swp', '*.pyc', '.gitignore', '.svnignore'}
    def __init__(self, config_file, project_dir, language_hints=None, exclude_dirs=None, exclude_files=None):
        super().__init__(project_dir)
        self.config = StatCodeConfig(config_file)
        language_config = self.config.get_language_config()
        self.language_classifier = LanguageClassifier(language_config)
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
        self._directories = {}
        self.classify()

    def num_projects(self):
        return 1

    def classify(self):
        self.project_tree = ProjectTree(self.project_dir, None, self)
        self.project_tree.post_classify()
        self.merge_tree(self.project_tree)

#    def most_common_languages(self):
#        for language, files in sorted(((language, files) for language, files in self.tree_language_project_files.items()), key=lambda x: -len(x[1])):
#            yield language
        
    def language_hints(self):
        return iter(self._language_hints)

class MetaProject(BaseProject):
    def __init__(self, projects=None):
        super().__init__('MetaProject')
        self.projects = []
        if projects:
            for project in projects:
                self.add_project(project)

    def add_project(self, project):
        if not isinstance(project, BaseProject):
            project = Project(project)
        self.merge_project(project)
        self.projects.append(project)
            
    def num_projects(self):
        return sum((project.num_projects() for project in self.projects), 0)

    def __iter__(self):
        return iter(self.projects)

    def __len__(self):
        return len(self.projects)

    def __getitem__(self, index):
        return self.projects[index]

    def sort_projects(self, *, sort_keys=None):
        pl = [(project.project_entry(), project) for project in self.projects]
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in ProjectEntry._fields:
                    continue
            pl.sort(key=lambda x: getattr(x[0], sort_key.key), reverse=sort_key.reverse)
        self.projects = [x[1] for x in pl]

    def report(self, *, print_function=print, sort_keys=None, patterns=None, pattern_type=None):
        self.sort_projects(sort_keys=sort_keys)
        for project in self.projects:
            project.report(print_function=print_function, sort_keys=sort_keys, patterns=patterns, pattern_type=pattern_type)

        if len(self.projects) > 1:
            super().report(print_function=print_function, sort_keys=sort_keys, patterns=patterns, pattern_type=pattern_type)
            print("PROJECTS: {}".format(self.num_projects()))

    def _list_language_files(self, language, *, print_function=print, sort_keys=None):
        self.sort_projects(sort_keys=sort_keys)
        for project in self.projects:
            project._list_language_files(language, print_function=print_function, sort_keys=sort_keys)

        if len(self.projects) > 1:
            super()._list_language_files(language, print_function=print_function, sort_keys=sort_keys)
            print("PROJECTS: {}".format(self.num_projects()))
