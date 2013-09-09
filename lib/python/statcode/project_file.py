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

from .stats import FileStats
from .language_classifier import LanguageClassifier

class ProjectFile(object):
    def __init__(self, filepath, project_dir, language=None):
        self.project_dir = project_dir
        self.language_classifier = project_dir.project.language_classifier
        self.filepath = filepath
        self._languages = None
        self.qualifiers = None
        self.language = language
        self.stats = None

    def pre_classify(self):
        qualifiers, self._languages = self.language_classifier.classify(self.filepath)
        if qualifiers:
            self.qualifiers = ";".join(qualifiers) + '-'
        if self._languages is not None:
            if len(self._languages) == 0:
                self.language = LanguageClassifier.LANGUAGE_UNCLASSIFIED
            elif len(self._languages) == 1:
                self.language = next(iter(self._languages))
        #print("PRE", self.filepath, self._languages, self.language)

    def post_classify(self):
#        if self.filepath.endswith(".h"):
#            print("***", self.filepath, self.language, self._languages)
        if self.language is None:
            if self._languages is None:
                self.language = LanguageClassifier.LANGUAGE_UNCLASSIFIED
            else:
                project_dir = self.project_dir
                while project_dir:
                    for language in project_dir.most_common_languages():
                        assert not language in LanguageClassifier.NO_LANGUAGE_FILES
                        if language in self._languages:
                            self.language = language
                            #print("HERE A: ", self.filepath, self._languages, self.language, project_dir.dirpath)
                            break
                    else:
                        project_dir = project_dir.parent
                        continue
                    break
                else:
                    self.language = next(iter(self._languages))
                    #print("HERE Z: ", self.filepath, self._languages, self.language)

        # stats
        if self.language in LanguageClassifier.NON_TEXT_FILES:
            if self.language in LanguageClassifier.NON_EXISTENT_FILES:
                self.stats = FileStats()
            else:
                self.stats = FileStats(bytes=os.stat(self.filepath).st_size)
        else:
            if self.language_classifier.language_is_binary(self.language):
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
                except UnicodeDecodeError as e:
                    self.language = LanguageClassifier.LANGUAGE_DATA
                    self.stats = FileStats(bytes=os.stat(self.filepath).st_size)
        #print("POST", self.filepath, self._languages, self.language)
        
        
