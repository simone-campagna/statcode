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

from .project_dir import ProjectDir
from .stats import DirStats, TreeStats

class BaseTree(object):
    def __init__(self):
        self.tree_language_project_files = collections.defaultdict(list)
        self.tree_language_stats = collections.defaultdict(TreeStats)
        self.tree_stats = TreeStats()

    def merge_tree(self, tree):
        for language, project_files in tree.tree_language_project_files.items():
            self.tree_language_project_files[language].extend(project_files)
            self.tree_language_stats[language] += tree.tree_language_stats[language]
        self.tree_stats += tree.tree_stats

class ProjectTree(ProjectDir, BaseTree):
    def __init__(self, dirpath, parent, project, language=None):
        BaseTree.__init__(self)
        super().__init__(dirpath, parent=parent, project=project, language=language)
        self.post_classify()
        self.make_tree_stats()

#    def post_classify(self):
#        super().post_classify()
#        self.make_tree_stats()

    def make_tree_stats(self):
        self.tree_language_project_files.clear()
        self.tree_language_stats.clear()
        self.tree_stats.clear()
        self._update_tree_stats(
            self.tree_language_project_files,
            self.tree_language_stats,
            self.tree_stats
        )
