#!/usr/bin/env python3

import os
import abc
import fnmatch
import collections

from .stats import FileStats, DirStats, TreeStats
from .project_file import ProjectFile
from .project_dir import ProjectDir
from .project_tree import ProjectTree

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

class BaseProject(metaclass=abc.ABCMeta):
    def __init__(self, name):
        self.name = name
        self.language_project_files = collections.defaultdict(list)
        self.language_dir_stats = collections.defaultdict(DirStats)
        self.tot_stats = DirStats()

    def project_entry(self):
        return ProjectEntry(projects=self.num_projects(), files=self.tot_stats.files, lines=self.tot_stats.lines, bytes=self.tot_stats.bytes)

    @abc.abstractmethod
    def num_projects(self):
        pass

    def merge_project(self, project):
        assert isinstance(project, BaseProject)
        for language, project_files in project.language_project_files.items():
            self.language_project_files[language].extend(project_files)
            self.language_dir_stats[language] += project.language_dir_stats[language]
        self.tot_stats += project.tot_stats

    def report(self, *, print_function=print, sort_keys=None):
        if self.name:
            print("=== Project[{}]".format(self.name))
        tot_stats = DirStats()
        languages = sorted(self.language_project_files.keys(), key=lambda x: x.lower())
        fmt_header = "{:16} {:>12s} {:>12s} {:>12s}"
        fmt_data = "{:16} {:12d}"
        fmt_code = fmt_data + " {:12d} {:12d}"
        print_function(fmt_header.format('LANGUAGE', '#FILES', '#LINES', '#BYTES'))
        table = []
        for language, language_stats in self.language_dir_stats.items():
            table.append(DirEntry(
                language=language,
                files=language_stats.files,
                lines=language_stats.lines,
                bytes=language_stats.bytes))

        table.sort(key=lambda x: x.language)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in DirEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            if ProjectFile.language_has_stats(entry.language):
                fmt = fmt_code
            else:
                fmt = fmt_data
            print_function(fmt.format(entry.language, entry.files, entry.lines, entry.bytes))
        print_function(fmt_code.format('TOTAL', self.tot_stats.files, self.tot_stats.lines, self.tot_stats.bytes))
        print_function()

    def list_language_files(self, language, *, print_function=print, sort_keys=None):
        if self.name:
            print("=== Project[{}]".format(self.name))
        if not language in self.language_project_files:
            return

        fmt_header = "{:16} {:>12s} {:>12s} {}"
        fmt_data = "{:16}"
        fmt_code = fmt_data + " {:12d} {:12d} {}"
        print_function(fmt_header.format('LANGUAGE', '#LINES', '#BYTES', 'FILENAME'))
        table = []
        tot_stats = DirStats()
        for project_file in self.language_project_files[language]:
            stats = project_file.stats
            tot_stats += stats
            table.append(FileEntry(language=language, lines=stats.lines, bytes=stats.bytes, filepath=project_file.filepath))

        table.sort(key=lambda x: x.language)
        if sort_keys:
            for sort_key in sort_keys:
                assert isinstance(sort_key, SortKey)
                if not sort_key.key in FileEntry._fields:
                    continue
                table.sort(key=lambda x: getattr(x, sort_key.key), reverse=sort_key.reverse)

        for entry in table:
            if ProjectFile.language_has_stats(entry.language):
                fmt = fmt_code
            else:
                fmt = fmt_data
            print_function(fmt.format(entry.language, entry.lines, entry.bytes, entry.filepath))
        print_function(fmt_code.format('TOTAL', tot_stats.lines, tot_stats.bytes, ''))
        print_function()


class Project(BaseProject):
    EXCLUDE_DIRS = {'.git', '.svn', 'CVS', '__pycache__'}
    EXCLUDE_FILES = {'.*.swp', '*.pyc', '.gitignore', '.svnignore'}
    def __init__(self, project_dir, language_hints=None, exclude_dirs=None, exclude_files=None):
        super().__init__(project_dir)
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
#        project_tree = ProjectTree(self.project_dir, None, self)
#        print(project_tree.dir_stats)
#        print(project_tree.tree_stats)
        unclassified_files = []
        for dirpath, dirnames, filenames in os.walk(self.project_dir, topdown=True):
            excluded_dirnames = set()
            for dir_pattern in self.exclude_dirs:
                excluded_dirnames.update(fnmatch.filter(dirnames, dir_pattern))
            if excluded_dirnames:
                #print("excluded_dirnames=", excluded_dirnames)
                filtered_dirnames = list(filter(lambda dirname: not dirname in excluded_dirnames, dirnames))
                del dirnames[:]
                dirnames.extend(filtered_dirnames)
            excluded_filenames = set()
            for file_pattern in self.exclude_files:
                excluded_filenames.update(fnmatch.filter(filenames, file_pattern))
            if excluded_filenames:
                #print("excluded_filenames=", excluded_filenames)
                filenames = list(filter(lambda filename: not filename in excluded_filenames, filenames))
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                project_file = ProjectFile(filepath, self)
                if project_file.language:
                    self.language_project_files[project_file.language].append(project_file)
                else:
                    unclassified_files.append(project_file)
        for project_file in unclassified_files:
            project_file.post_classify()
            self.language_project_files[project_file.language].append(project_file)
        for language, project_files in self.language_project_files.items():
            language_stats = DirStats()
            for project_file in project_files:
                language_stats += project_file.stats
            self.language_dir_stats[language] = language_stats
            if ProjectFile.language_has_stats(language):
                self.tot_stats += language_stats

    def most_common_languages(self):
        for language, files in sorted(((language, files) for language, files in self.language_project_files.items()), key=lambda x: -len(x[1])):
            yield language
        
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

    def report(self, *, print_function=print, sort_keys=None):
        self.sort_projects(sort_keys=sort_keys)
        for project in self.projects:
            project.report(print_function=print_function, sort_keys=sort_keys)

        if len(self.projects) > 1:
            super().report(print_function=print_function, sort_keys=sort_keys)
            print("PROJECTS: {}".format(self.num_projects()))

    def list_language_files(self, language, *, print_function=print, sort_keys=None):
        self.sort_projects(sort_keys=sort_keys)
        for project in self.projects:
            project.list_language_files(language, print_function=print_function, sort_keys=sort_keys)

        if len(self.projects) > 1:
            super().list_language_files(language, print_function=print_function, sort_keys=sort_keys)
            print("PROJECTS: {}".format(self.num_projects()))
