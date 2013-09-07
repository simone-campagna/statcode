#!/usr/bin/env python3

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
        

    def classify(self):
        super().classify()
        self.make_tree_stats()

    def make_tree_stats(self):
        self.tree_language_project_files.clear()
        self.tree_language_stats.clear()
        self.tree_stats.clear()
        self._update_tree_stats(
            self.tree_language_project_files,
            self.tree_language_stats,
            self.tree_stats
        )
