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
from .filetype_classifier import FileTypeClassifier
from .statcode_config import StatCodeConfig
from .project_file import ProjectFile
from .project_dir import ProjectDir
from .project_tree import ProjectTree, BaseTree
from . import patternutils

DirEntry = collections.namedtuple('DirEntry', ('filetype', 'files', 'lines', 'bytes'))
FileEntry = collections.namedtuple('FileEntry', ('filetype', 'lines', 'bytes', 'filepath'))
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
        filetypes = sorted(self.tree_filetype_project_files.keys(), key=lambda x: x.lower())
        fmt_header = "{filetype:16} {files:>12s} {lines:>12s} {bytes:>12s}"
        fmt_data = "{filetype:16} {files:12d} {lines:12d} {bytes:12d}"
        fmt_code = "{filetype:16} {files:12d} {lines:12d} {bytes:12d}"
        print_function(fmt_header.format(filetype='FILETYPE', files='#FILES', lines='#LINES', bytes='#BYTES', null=''))
        table = []
        tree_stats = TreeStats()
        filetypes = set(self.tree_filetype_stats.keys())
        if pattern_type == '-':
            for pattern in patterns:
                filetypes.difference_update(fnmatch.filter(filetypes, pattern))
        else:
            selected_filetypes = set()
            for pattern in patterns:
                selected_filetypes.update(fnmatch.filter(filetypes, pattern))
            filetypes = selected_filetypes
        for filetype in filetypes:
            filetype_stats = self.tree_filetype_stats[filetype]
            table.append(DirEntry(
                filetype=filetype,
                files=filetype_stats.files,
                lines=filetype_stats.lines,
                bytes=filetype_stats.bytes))
            tree_stats += filetype_stats

        table.sort(key=lambda x: x.filetype)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in DirEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            if FileTypeClassifier.filetype_has_lines_stats(entry.filetype):
                fmt = fmt_code
            else:
                fmt = fmt_data
            print_function(fmt.format(filetype=entry.filetype, files=entry.files, lines=entry.lines, bytes=entry.bytes, null=''))
        print_function(fmt_code.format(filetype='TOTAL', files=tree_stats.files, lines=tree_stats.lines, bytes=tree_stats.bytes, null=''))
        print_function()

    def list_filetype_files(self, filetype_pattern, *, print_function=print, sort_keys=None):
        filetypes = []
        for filetype in self.tree_filetype_project_files:
            if fnmatch.fnmatchcase(filetype, filetype_pattern):
                filetypes.append(filetype)
        self.list_filetypes_files(filetypes, print_function=print_function, sort_keys=sort_keys)

    def list_filetypes_files(self, filetypes, *, print_function=print, sort_keys=None):
        if self.name:
            print("=== Project[{}]".format(self.name))

        fmt_header = "{filetype:16s} {lines:>12s} {bytes:>12s} {file}"
        fmt_data = "{filetype:16s} {lines:12d} {bytes:12d} {file}"
        fmt_code = "{filetype:16s} {lines:12d} {bytes:12d} {file}"
        print_function(fmt_header.format(filetype='FILETYPE', lines='#LINES', bytes='#BYTES', file='FILENAME', null=''))
        table = []
        tree_stats = TreeStats()
        for filetype in filetypes:
            if not filetype in self.tree_filetype_project_files:
                continue
            for project_file in self.tree_filetype_project_files[filetype]:
                stats = project_file.stats
                tree_stats += stats
                table.append(FileEntry(filetype=filetype, lines=stats.lines, bytes=stats.bytes, filepath=project_file.filepath))
    
        table.sort(key=lambda x: x.filetype)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in FileEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            if FileTypeClassifier.filetype_has_lines_stats(entry.filetype):
                fmt = fmt_code
            else:
                fmt = fmt_data
            print_function(fmt.format(filetype=entry.filetype, lines=entry.lines, bytes=entry.bytes, file=entry.filepath, null=''))
        print_function(fmt_code.format(filetype='TOTAL', lines=tree_stats.lines, bytes=tree_stats.bytes, file='', null=''))
        print_function()


class Project(BaseProject):
    def __init__(self, config, project_dir, filetype_hints=None):
        super().__init__(project_dir)
        if isinstance(config, str):
            config = StatCodeConfig(config)
        assert isinstance(config, StatCodeConfig)
        self.config = config
        filetype_config = self.config.get_filetype_config()
        qualifier_config = self.config.get_qualifier_config()
        self.filetype_classifier = FileTypeClassifier(filetype_config, qualifier_config)
        self.project_dir = project_dir
        if filetype_hints is None:
            filetype_hints = ()
        directory_config = self.config.get_directory_config()
        self.exclude_dir_names = set()
        self.exclude_dir_matchers = set()
        self.exclude_file_names = set()
        self.exclude_file_matchers = set()
        for section_name in directory_config.sections():
            section = directory_config[section_name]
            dir_names, dir_matchers = patternutils.filter_patterns(directory_config.string_to_list(section['exclude_dir_patterns']))
            self.exclude_dir_names.update(dir_names)
            self.exclude_dir_matchers.update(dir_matchers)
            file_names, file_matchers = patternutils.filter_patterns(directory_config.string_to_list(section['exclude_file_patterns']))
            self.exclude_file_names.update(file_names)
            self.exclude_file_matchers.update(file_matchers)
        #print("exclude_dir_names={}".format(self.exclude_dir_names))
        #print("exclude_dir_matchers={}".format(self.exclude_dir_matchers))
        #print("exclude_file_names={}".format(self.exclude_file_names))
        #print("exclude_file_matchers={}".format(self.exclude_file_matchers))
        assert isinstance(filetype_hints, collections.Sequence)
        self._filetype_hints = filetype_hints
        self._directories = {}
        self.classify()

    def num_projects(self):
        return 1

    def classify(self):
        self.project_tree = ProjectTree(self.project_dir, None, self)
        self.project_tree.post_classify()
        self.merge_tree(self.project_tree)

#    def most_common_filetypes(self):
#        for filetype, files in sorted(((filetype, files) for filetype, files in self.tree_filetype_project_files.items()), key=lambda x: -len(x[1])):
#            yield filetype
        
    def filetype_hints(self):
        return iter(self._filetype_hints)

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

#    def _list_filetype_files(self, filetype, *, print_function=print, sort_keys=None):
#        self.sort_projects(sort_keys=sort_keys)
#        for project in self.projects:
#            project._list_filetype_files(filetype, print_function=print_function, sort_keys=sort_keys)
#
#        if len(self.projects) > 1:
#            super()._list_filetype_files(filetype, print_function=print_function, sort_keys=sort_keys)
#            print("PROJECTS: {}".format(self.num_projects()))
