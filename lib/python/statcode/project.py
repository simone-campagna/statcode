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

DirEntry = collections.namedtuple('DirEntry', ('category', 'filetype', 'files', 'lines', 'bytes'))
FileEntry = collections.namedtuple('FileEntry', ('category', 'filetype', 'lines', 'bytes', 'filepath'))
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

class ProjectConfiguration(object):
    def __init__(self, config):
        if isinstance(config, str):
            config = StatCodeConfig(config)
        assert isinstance(config, StatCodeConfig)
        self.config = config
        self.filetype_config = self.config.get_filetype_config()
        self.qualifier_config = self.config.get_qualifier_config()
        self.directory_config = self.config.get_directory_config()
        self.filetype_classifier = FileTypeClassifier(self.filetype_config, self.qualifier_config)

class BaseProject(BaseTree, metaclass=abc.ABCMeta):
    def __init__(self, configuration, name):
        assert isinstance(configuration, ProjectConfiguration)
        self.configuration = configuration
        self.config = self.configuration.config
        self.filetype_config = self.configuration.filetype_config
        self.qualifier_config = self.configuration.qualifier_config
        self.directory_config = self.configuration.directory_config
        self.filetype_classifier = self.configuration.filetype_classifier
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


    def _category_filetypes(self, filetypes, group_categories):
        categories = set((self.filetype_classifier.get_category(filetype) for filetype in filetypes))
        category_group = {}
        for category in categories:
            group = False
            for category_pattern in group_categories:
                sign, category_pattern = patternutils.get_signed_pattern(category_pattern)
                if fnmatch.fnmatchcase(category, category_pattern):
                    if sign == patternutils.NEGATE_PATTERN:
                        group = False
                    else:
                        group = True
                category_group[category] = group

        category_filetypes = []
        category_d = collections.defaultdict(list)
        for filetype in filetypes:
            category = self.filetype_classifier.get_category(filetype)
            if category_group[category]:
                category_d[category].append(filetype)
            else:
                category_filetypes.append((category, (filetype, )))

        category_filetypes.extend(category_d.items())
        return category_filetypes
        
    def report(self, *, print_function=print, sort_keys=None, select_filetypes=None, group_categories=None):
        if self.name:
            print("=== Project[{}]".format(self.name))
        if select_filetypes is None:
            select_filetypes = []
        if group_categories is None:
            group_categories = []
        filetypes = sorted(self.tree_filetype_project_files.keys(), key=lambda x: x.lower())
        fmt_header = "{category:16} {filetype:16} {files:>12s} {lines:>12s} {bytes:>12s}"
        fmt_body = "{category:16} {filetype:16} {files:12d} {lines:12d} {bytes:12d}"
        print_function(fmt_header.format(category='CATEGORY', filetype='FILETYPE', files='#FILES', lines='#LINES', bytes='#BYTES', null=''))
        table = []
        tree_stats = TreeStats()
        all_filetypes = set(self.tree_filetype_stats.keys())

        filetypes = patternutils.apply_signed_patterns(all_filetypes, select_filetypes)
        #print(all_filetypes)
        #print(filetypes)
        #input("...")

        category_filetypes = self._category_filetypes(filetypes, group_categories)

        for category, filetypes in category_filetypes:
            if len(filetypes) == 1:
                category_filetype = filetypes[0]
                category_stats = self.tree_filetype_stats[category_filetype]
            else:
                category_stats = TreeStats()
                for filetype in filetypes:
                    category_stats += self.tree_filetype_stats[filetype]
                category_filetype = ''
            table.append(DirEntry(
                category=category,
                filetype=category_filetype,
                files=category_stats.files,
                lines=category_stats.lines,
                bytes=category_stats.bytes))
            tree_stats += category_stats

        table.sort(key=lambda x: x.filetype)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in DirEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            print_function(fmt_body.format(category=entry.category, filetype=entry.filetype, files=entry.files, lines=entry.lines, bytes=entry.bytes, null=''))
        print_function(fmt_body.format(category='', filetype='TOTAL', files=tree_stats.files, lines=tree_stats.lines, bytes=tree_stats.bytes, null=''))
        print_function()

    def list_filetype_files(self, filetype_patterns, *, print_function=print, sort_keys=None):
        all_filetypes = set(self.tree_filetype_project_files.keys())
        filetypes = patternutils.apply_signed_patterns(set(self.tree_filetype_project_files.keys()), filetype_patterns)
        self.list_filetypes_files(filetypes, print_function=print_function, sort_keys=sort_keys)

    def list_filetypes_files(self, filetypes, *, print_function=print, sort_keys=None):
        if self.name:
            print("=== Project[{}]".format(self.name))

        fmt_header = "{category:16} {filetype:16s} {lines:>12s} {bytes:>12s} {file}"
        fmt_body = "{category:16} {filetype:16s} {lines:12d} {bytes:12d} {file}"
        print_function(fmt_header.format(category='CATEGORY', filetype='FILETYPE', lines='#LINES', bytes='#BYTES', file='FILENAME', null=''))
        table = []
        tree_stats = TreeStats()
        for filetype in filetypes:
            if not filetype in self.tree_filetype_project_files:
                continue
            category = self.filetype_classifier.get_category(filetype)
            for project_file in self.tree_filetype_project_files[filetype]:
                stats = project_file.file_stats
                tree_stats += stats
                table.append(FileEntry(category=category, filetype=filetype, lines=stats.lines, bytes=stats.bytes, filepath=project_file.filepath))
    
        table.sort(key=lambda x: x.filetype)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in FileEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            print_function(fmt_body.format(category=entry.category, filetype=entry.filetype, lines=entry.lines, bytes=entry.bytes, file=entry.filepath, null=''))
        print_function(fmt_body.format(category='', filetype='TOTAL', lines=tree_stats.lines, bytes=tree_stats.bytes, file='', null=''))
        print_function()



class Project(BaseProject):
    def __init__(self, configuration, project_dir, filetype_hints=None, block_size=None, progress_bar=None):
        super().__init__(configuration, project_dir)
        self.project_dir = project_dir
        filetype_config = self.filetype_config
        directory_config = self.directory_config
        qualifier_config = self.qualifier_config

        if filetype_hints is None:
            filetype_hints = ()
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
        assert isinstance(filetype_hints, collections.Sequence)
        self._filetype_hints = filetype_hints
        self._directories = {}
        if block_size is None:
            block_size = 1024 * 1024
        self.block_size = block_size
        self.progress_bar = progress_bar
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
    def __init__(self, configuration, projects=None, progress_bar=None):
        super().__init__(configuration, 'MetaProject')
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

    def report(self, *, print_function=print, sort_keys=None, **n_args):
        self.sort_projects(sort_keys=sort_keys)
        for project in self.projects:
            project.report(print_function=print_function, sort_keys=sort_keys, **n_args)

        if len(self.projects) > 1:
            super().report(print_function=print_function, sort_keys=sort_keys, **n_args)
            print("PROJECTS: {}".format(self.num_projects()))

    def list_filetype_files(self, filetype_patterns, *, print_function=print, sort_keys=None, **n_args):
        self.sort_projects(sort_keys=sort_keys)
        for project in self.projects:
            project.list_filetype_files(filetype_patterns, print_function=print_function, sort_keys=sort_keys, **n_args)

        if len(self.projects) > 1:
            super().list_filetype_files(filetype_patterns, print_function=print_function, sort_keys=sort_keys, **n_args)
            print("PROJECTS: {}".format(self.num_projects()))
        
#    def _list_filetype_files(self, filetype, *, print_function=print, sort_keys=None):
#        self.sort_projects(sort_keys=sort_keys)
#        for project in self.projects:
#            project._list_filetype_files(filetype, print_function=print_function, sort_keys=sort_keys)
#
#        if len(self.projects) > 1:
#            super()._list_filetype_files(filetype, print_function=print_function, sort_keys=sort_keys)
#            print("PROJECTS: {}".format(self.num_projects()))
