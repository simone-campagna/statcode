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
import fnmatch
import collections

from .filetype_classifier import FileTypeClassifier
from .project_file import ProjectFile
from .stats import DirStats, TreeStats
from . import patternutils

class ProjectDir(object):
    def __init__(self, dirpath, parent, project, filetype=None):
        self.dirpath = dirpath
        self.parent = parent
        self.project = project
        self.filetype = filetype
        self.dir_filetype_project_files = collections.defaultdict(list)
        self.dir_filetype_stats = collections.defaultdict(DirStats)
        self.dir_stats = DirStats()
        self.project_dirs = []
        self.project_files = []
        if self.parent:
            self.level = self.parent.level + 1
            self.parent_progress_bar = getattr(self.parent, 'progress_bar', None)
        else:
            self.level = 0
            self.parent_progress_bar = self.project.progress_bar
        self.pre_classify()

    def most_common_filetypes(self):
        filetypes = set(self.dir_filetype_project_files.keys()).difference(FileTypeClassifier.NO_FILETYPE_FILES)
        l = sorted(((filetype, len(self.dir_filetype_project_files[filetype])) for filetype in filetypes),
                    key=lambda x: -x[-1])
        for filetype, num_files in l:
            yield filetype
   
    def filetype_hints(self):
        return self.project.filetype_hints()

    def _add_dir(self, dirpath):
        project_dir = ProjectDir(dirpath, self, self.project, filetype=self.filetype)
        self.project_dirs.append(project_dir)

    def _add_file(self, filepath):
        project_file = ProjectFile(filepath, self, filetype=self.filetype)
        self.project_files.append(project_file)

    def _register_project_file(self, project_file):
        #print("reg: ", project_file.filepath, project_file.filetype, project_file.file_stats)
        self.dir_filetype_project_files[project_file.filetype].append(project_file)

#    def _patterns_match(self, names, patterns, name):
#        if name in names:
#            return True
#        for pattern in patterns:
#            if fnmatch.fnmatch(name, pattern):
#                return True
#        return False

    def pre_classify(self):
        real_dirpath = os.path.realpath(self.dirpath)
        self.progress_bar = None
        if not os.path.isdir(real_dirpath):
            return

        exclude_dir_names = self.project.exclude_dir_names
        exclude_dir_matchers = self.project.exclude_dir_matchers
        exclude_file_names = self.project.exclude_file_names
        exclude_file_matchers = self.project.exclude_file_matchers

        dirnames = []
        filenames = []
        try:
            names = os.listdir(self.dirpath)
        except OSError as e:
            names = ()
            pass
        for name in names:
            pathname = os.path.join(self.dirpath, name)
            realpathname = os.path.realpath(pathname)
            if os.path.isdir(realpathname):
                if not patternutils.match_names_or_matchers(exclude_dir_names, exclude_dir_matchers, name):
                    dirnames.append(pathname)
            else:
                if not patternutils.match_names_or_matchers(exclude_file_names, exclude_file_matchers, name):
                    filenames.append(pathname)

        if self.level < self.project.progress_bar_level:
            intervals = 2 * len(dirnames) + 3 * len(filenames)
            if intervals:
                progress_bar = self.parent_progress_bar.sub_progress_bar(intervals=intervals)
            else:
                progress_bar = None
        else:
            progress_bar = None
        self.progress_bar = progress_bar

        if progress_bar:
            for pathname in dirnames:
                self._add_dir(pathname)
                progress_bar.render(basedir=pathname[-10:])
            for pathname in filenames:
                self._add_file(pathname)
                progress_bar.render(basedir=pathname[-10:])
        else:
            for pathname in dirnames:
                self._add_dir(pathname)
            for pathname in filenames:
                self._add_file(pathname)

        # pre
        if progress_bar:
            for project_file in self.project_files:
                project_file.pre_classify()
                if project_file.filetype is not None:
                    self._register_project_file(project_file)
                progress_bar.render(basedir=project_file.filepath[-10:])
        else:
            for project_file in self.project_files:
                project_file.pre_classify()
                if project_file.filetype is not None:
                    self._register_project_file(project_file)


    def post_classify(self):
        progress_bar = self.progress_bar

        # post
        for project_file in self.project_files:
            must_register = project_file.filetype is None
            project_file.post_classify()
            if must_register:
                self._register_project_file(project_file)
            if progress_bar:
                progress_bar.render(basedir=project_file.filepath[-10:])

        # dir stats
        for project_file in self.project_files:
            self.dir_stats += project_file.file_stats
            self.dir_filetype_stats[project_file.filetype] += project_file.file_stats
            if progress_bar:
                progress_bar.render(basedir=project_file.filepath[-10:])

        for project_dir in self.project_dirs:
            project_dir.post_classify()
            if progress_bar:
                progress_bar.render(basedir=project_dir.dirpath[-10:])

#    def get_tree_stats(self):
#        tree_filetype_project_files = collections.defaultdict(list)
#        tree_filetype_stats = collections.defaultdict(TreeStat)
#        tree_stats = TreeStats()
#        self._update_tree_stats(
#            tree_filetype_project_files,
#            tree_filetype_stats,
#            tree_stats)
#        return (tree_filetype_project_files, tree_filetype_stats, tree_stats)

    def _update_tree_stats(self,
                        tree_filetype_project_files,
                        tree_filetype_stats,
                        tree_stats):
        for filetype, project_files in self.dir_filetype_project_files.items():
            tree_filetype_project_files[filetype].extend(project_files)
            tree_filetype_stats[filetype] += self.dir_filetype_stats[filetype]
        tree_stats += self.dir_stats
        tree_stats.dirs += 1
        for project_dir in self.project_dirs:
            project_dir._update_tree_stats(
                        tree_filetype_project_files,
                        tree_filetype_stats,
                        tree_stats)
