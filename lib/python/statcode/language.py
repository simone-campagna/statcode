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
import re
import fnmatch
import collections


class LanguageClassifier(object):
    SHEBANG = '#!'
    LANGUAGE_DATA = '{data}'
    LANGUAGE_BROKEN_LINK = '{broken-link}'
    LANGUAGE_NO_FILE = '{no-file}'
    LANGUAGE_UNCLASSIFIED = '{unclassified}'
    NO_LANGUAGE_FILES = {LANGUAGE_DATA, LANGUAGE_BROKEN_LINK, LANGUAGE_NO_FILE, LANGUAGE_UNCLASSIFIED}
    BINARY_FILES = {LANGUAGE_DATA}
    NON_TEXT_FILES = {LANGUAGE_DATA, LANGUAGE_BROKEN_LINK, LANGUAGE_NO_FILE}
    NON_EXISTENT_FILES = {LANGUAGE_BROKEN_LINK, LANGUAGE_NO_FILE}
    def __init__(self, language_config):
        self._file_extensions = collections.defaultdict(set)
        self._file_extension_re_patterns = collections.defaultdict(set)
        self._file_re_patterns = collections.defaultdict(set)
        self._interpreter_re_patterns = collections.defaultdict(set)
        # from language_config
        for language in language_config.sections():
            section = language_config[language]
            for extension in language_config.string_to_list(section['file_extensions']):
                self._file_extensions[os.path.extsep + extension].add(language)
            for pattern in language_config.string_to_list(section['file_patterns']):
                re_pattern = re.compile(fnmatch.translate(pattern))
                patternroot, patternext = os.path.splitext(pattern)
                for extension in self._file_extensions:
                    if fnmatch.fnmatch(extension, patternext):
                        self._file_extension_re_patterns[extension].add(re_pattern)
                self._file_re_patterns[re_pattern].add(language)
            for pattern in language_config.string_to_list(section['interpreter_patterns']):
                re_pattern = re.compile(fnmatch.translate(pattern))
                self._interpreter_re_patterns[re_pattern].add(language)

#    def classify_file(self, filehandle, filepath=None, filename=None):
#        if filepath is None:
#            filepath = filehandle.name # it can fail!
#        languages = self.classify_by_filename(filepath, filename)
#        if languages is None:
#            languages = self.classify_by_content(filehandle, filepath, filename)
#        return languages

    def classify(self, filepath, filename=None):
        languages = None
        if not os.path.exists(os.path.realpath(filepath)):
            if os.path.lexists(filepath):
                return {self.LANGUAGE_BROKEN_LINK}
            else:
                return {self.LANGUAGE_NO_FILE}

        if filename is None:
            filename = os.path.basename(filepath)
   
        languages = self.classify_by_filename(filepath, filename)

        if languages is None:
            try:
                with open(filepath, 'r') as filehandle:
                    languages = self.classify_by_content(filehandle, filepath, filename)
            except UnicodeDecodeError:
                languages = {self.LANGUAGE_DATA}

        return languages

    def classify_by_filename(self, filepath, filename):
        fileroot, fileext = os.path.splitext(filename)
        # by extension
        if fileext in self._file_extensions:
            if fileext in self._file_extension_re_patterns:
                # by pattern
                for re_pattern in self._file_extension_re_patterns[fileext]:
                    if re_pattern.match(filename):
                        return self._file_re_patterns[re_pattern]
            return self._file_extensions[fileext]
        # by pattern
        for re_pattern, languages in self._file_re_patterns.items():
            if re_pattern.match(filename):
                return languages
        return None

    def classify_by_content(self, filehandle, filepath, filename):
        return self.classify_by_shebang(filehandle, filepath, filename)

    def classify_by_shebang(self, filehandle, filepath, filename):
        try:
            first_line = filehandle.readline().rstrip()
            if first_line.startswith(self.SHEBANG):
                fl = [e.strip() for e in first_line[len(self.SHEBANG):].split()]
                if fl:
                    if fl[0] == '/usr/bin/env' and len(fl) > 1:
                        interpreter = fl[1]
                    else:
                        interpreter = fl[0]
                interpreter = os.path.basename(interpreter)
                for re_pattern, languages in self._interpreter_re_patterns.items():
                    if re_pattern.match(interpreter):
                        return languages
                        break
                else:
                    languages = {interpreter}
                    return languages
            else:
                # no shebang
                return None
        except UnicodeDecodeError:
            languages = {self.LANGUAGE_DATA}
            return languages
        
    @classmethod
    def language_has_lines_stats(cls, language):
        return not language in cls.NON_TEXT_FILES

if __name__ == "__main__":
    language_classifier = LanguageClassifier('languages.ini', 'interpreter.ini')
    import sys
    for arg in sys.argv[1]:
        print(arg, language_classifier.classify(arg))
