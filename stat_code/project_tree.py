#!/usr/bin/env python3

import os
import fnmatch
import collections

from .project_dir import ProjectDir
from .stats import DirStats, TreeStats

class ProjectTree(ProjectDir):
    def __init__(self, dirpath, parent, project, language=None):
        self.tree_language_project_files = collections.defaultdict(list)
        self.tree_language_stats = collections.defaultdict(TreeStats)
        self.tree_stats = TreeStats()
        print("START:", id(self.tree_stats))
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
