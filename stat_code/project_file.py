#!/usr/bin/env python3

import os
import fnmatch
import collections

from .stats import FileStats
from .language import LanguageClassifier

class ProjectFile(object):
    def __init__(self, filepath, project_dir, language=None):
        self.project_dir = project_dir
        self.filepath = filepath
        self._languages = None
        self.language = language
        self.stats = None

    def pre_classify(self):
        self._languages = self.project_dir.project.language_classifier.classify(self.filepath)
        if self._languages is not None:
            if len(self._languages) == 0:
                self.language = LanguageClassifier.LANGUAGE_UNCLASSIFIED
            elif len(self._languages) == 1:
                self.language = next(iter(self._languages))
        #print("PRE", self.filepath, self._languages, self.language)

    def post_classify(self):
        if self.language is None:
            if self._languages is None:
                self.language = LanguageClassifier.LANGUAGE_UNCLASSIFIED
            else:
                for language in self.project_dir.most_common_languages():
                    assert not language in LanguageClassifier.NO_LANGUAGE_FILES
                    if language in self._languages:
                        self.language = language
                        break
                else:
                    self.language = LanguageClassifier.LANGUAGE_UNCLASSIFIED

        # stats
        if self.language in LanguageClassifier.NON_TEXT_FILES:
            if self.language in LanguageClassifier.NON_EXISTENT_FILES:
                self.stats = FileStats()
            else:
                self.stats = FileStats(bytes=os.stat(self.filepath).st_size)
        else:
            try:
                with open(self.filepath, 'r') as filehandle:
                    num_lines = 0
                    num_bytes = 0
                    for line in filehandle:
                        num_bytes += len(line)
                        num_lines += 1
                    self.stats = FileStats(lines=num_lines, bytes=num_bytes)
            except UnicodeDecodeError:
                self.language = LanguageClassifier.LANGUAGE_DATA
                self.stats = FileStats(bytes=os.stat(self.filepath).st_size)
        #print("POST", self.filepath, self._languages, self.language)
        
        
