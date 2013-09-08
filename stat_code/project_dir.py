#!/usr/bin/env python3

import os
import fnmatch
import collections

from .language import LanguageClassifier
from .project_file import ProjectFile
from .stats import DirStats, TreeStats

class ProjectDir(object):
    def __init__(self, dirpath, parent, project, language=None):
        self.dirpath = dirpath
        self.parent = parent
        self.project = project
        self.language = language
        self.dir_language_project_files = collections.defaultdict(list)
        self.dir_language_stats = collections.defaultdict(DirStats)
        self.dir_stats = DirStats()
        self.project_dirs = []
        self.project_files = []
        self.pre_classify()

    def most_common_languages(self):
        languages = set(self.dir_language_project_files.keys()).difference(LanguageClassifier.NO_LANGUAGE_FILES)
        l = sorted(((language, len(self.dir_language_project_files[language])) for language in languages),
                    key=lambda x: -x[-1])
        for language, num_files in l:
            yield language
   
    def language_hints(self):
        return self.project.language_hints()

    def _add_dir(self, dirpath):
        project_dir = ProjectDir(dirpath, self, self.project, language=self.language)
        self.project_dirs.append(project_dir)

    def _add_file(self, filepath):
        project_file = ProjectFile(filepath, self, language=self.language)
        self.project_files.append(project_file)

    def _register_project_file(self, project_file):
        #print("reg: ", project_file.filepath, project_file.language, project_file.stats)
        self.dir_language_project_files[project_file.language].append(project_file)

    def _patterns_match(self, patterns, name):
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def pre_classify(self):
        real_dirpath = os.path.realpath(self.dirpath)
        if not os.path.isdir(real_dirpath):
            return

        exclude_dirs = self.project.exclude_dirs
        exclude_files = self.project.exclude_files

        for name in os.listdir(self.dirpath):
            pathname = os.path.join(self.dirpath, name)
            realpathname = os.path.realpath(pathname)
            if os.path.isdir(realpathname):
                if self._patterns_match(exclude_dirs, name):
                    continue
                self._add_dir(pathname)
            else:
                if self._patterns_match(exclude_files, name):
                    continue
                self._add_file(pathname)
    
        # pre
        for project_file in self.project_files:
            project_file.pre_classify()
            if project_file.language is not None:
                self._register_project_file(project_file)


    def post_classify(self):
        # post
        for project_file in self.project_files:
            must_register = project_file.language is None
            project_file.post_classify()
            if must_register:
                self._register_project_file(project_file)

        # dir stats
        for project_file in self.project_files:
            self.dir_stats += project_file.stats
            self.dir_language_stats[project_file.language] += project_file.stats

        for project_dir in self.project_dirs:
            project_dir.post_classify()

#    def get_tree_stats(self):
#        tree_language_project_files = collections.defaultdict(list)
#        tree_language_stats = collections.defaultdict(TreeStat)
#        tree_stats = TreeStats()
#        self._update_tree_stats(
#            tree_language_project_files,
#            tree_language_stats,
#            tree_stats)
#        return (tree_language_project_files, tree_language_stats, tree_stats)

    def _update_tree_stats(self,
                        tree_language_project_files,
                        tree_language_stats,
                        tree_stats):
        for language, project_files in self.dir_language_project_files.items():
            tree_language_project_files[language].extend(project_files)
            tree_language_stats[language] += self.dir_language_stats[language]
        tree_stats += self.dir_stats
        tree_stats.dirs += 1
        for project_dir in self.project_dirs:
            #print("+", self.dirpath, tree_stats, '+', project_dir.dirpath, project_dir.dir_stats)
            project_dir._update_tree_stats(
                        tree_language_project_files,
                        tree_language_stats,
                        tree_stats)
