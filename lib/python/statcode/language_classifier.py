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

from . import patternutils

class LanguageClassifier(object):
    SHEBANG = '#!'
    LANGUAGE_DATA = '{data}'
    LANGUAGE_BROKEN_LINK = '{broken-link}'
    LANGUAGE_NO_FILE = '{no-file}'
    LANGUAGE_UNREADABLE = '{unreadable}'
    LANGUAGE_UNCLASSIFIED = '{unclassified}'
    NO_LANGUAGE_FILES = {LANGUAGE_DATA, LANGUAGE_BROKEN_LINK, LANGUAGE_NO_FILE, LANGUAGE_UNCLASSIFIED, LANGUAGE_UNREADABLE}
    BINARY_FILES = {LANGUAGE_DATA}
    NON_TEXT_FILES = {LANGUAGE_DATA, LANGUAGE_BROKEN_LINK, LANGUAGE_NO_FILE, LANGUAGE_UNREADABLE}
    NON_EXISTENT_FILES = {LANGUAGE_BROKEN_LINK, LANGUAGE_NO_FILE, LANGUAGE_UNREADABLE}
    def __init__(self, language_config, qualifier_config):
        self._file_extensions = collections.defaultdict(set)
        self._file_extension_names = collections.defaultdict(set)
        self._file_extension_matchers = collections.defaultdict(set)
        self._file_names = collections.defaultdict(set)
        self._file_matchers = collections.defaultdict(set)
        self._interpreter_names = collections.defaultdict(set)
        self._interpreter_matchers = collections.defaultdict(set)
        self._binary_languages = set()
        # from language_config
        for language in language_config.sections():
            section = language_config[language]
            if language_config.string_to_bool(section['binary']):
                self._binary_languages.add(language)
            for extension in language_config.string_to_list(section['file_extensions']):
                self._file_extensions[os.path.extsep + extension].add(language)
            for pattern in language_config.string_to_list(section['file_patterns']):
                extensions = set()
                patternroot, patternext = os.path.splitext(pattern)
                for extension in self._file_extensions:
                    if fnmatch.fnmatch(extension, patternext):
                        extensions.add(extension)
                if patternutils.is_regular_expression(pattern):
                    matcher = patternutils.get_matcher(pattern)
                    self._file_matchers[matcher].add(language)
                    for extension in extensions:
                        self._file_extension_matchers[extension].add(matcher)
                else:
                    self._file_names[pattern].add(language)
                    for extension in extensions:
                        self._file_extension_names[extension].add(pattern)
            
            for pattern in language_config.string_to_list(section['interpreter_patterns']):
                if patternutils.is_regular_expression(pattern):
                    matcher = patternutils.get_matcher(pattern)
                    self._interpreter_matchers[matcher].add(language)
                else:
                    self._interpreter_names[pattern].add(language)

        # from qualifier_config
        self._qualifier = {}
        for extension in qualifier_config.sections():
            self._qualifier[os.path.extsep + extension] = qualifier_config.get_extension(extension)
 
    def classify(self, filepath, filename=None):
        languages = None
        if not os.path.exists(os.path.realpath(filepath)):
            if os.path.lexists(filepath):
                return [], {self.LANGUAGE_BROKEN_LINK}
            else:
                return [], {self.LANGUAGE_NO_FILE}

        if filename is None:
            filename = os.path.basename(filepath)
   
        fileroot, fileext = os.path.splitext(filename)
        qualifiers, languages = self.classify_by_filename(filename, fileroot, fileext)

        if languages is None:
            try:
                with open(filepath, 'r') as filehandle:
                    languages = self.classify_by_content(filehandle, filepath, filename)
            except UnicodeDecodeError:
                languages = {self.LANGUAGE_DATA}
            except IOError:
                languages = {self.LANGUAGE_UNREADABLE}

        return qualifiers, languages

    def classify_by_filename(self, filename, fileroot, fileext):
        qualifiers = []

        # qualifier, by extension
        qualifier = None
        if fileext in self._qualifier:
            qualifier, action = self._qualifier[fileext]
            qualifiers.append(qualifier)
            filename, fileroot, fileext = action(filename, fileroot, fileext)
            next_qualifiers, languages = self.classify_by_filename(filename, fileroot, fileext)
            qualifiers.extend(next_qualifiers)
        else:
            languages = self.classify_languages_by_filename(filename, fileroot, fileext)
        return qualifiers, languages

    def classify_languages_by_filename(self, filename, fileroot, fileext):
        # by extension
        if fileext in self._file_extensions:
            if fileext in self._file_extension_names:
                # by file name
                if filename in self._file_extension_names[fileext]:
                    return self._file_names[filename]
            if fileext in self._file_extension_matchers:
                # by file matcher
                for matcher in self._file_extension_matchers[fileext]:
                    if matcher(filename):
                        return self._file_matchers[matcher]
            return self._file_extensions[fileext]
        # by file name:
        if filename in self._file_names:
            return self._file_names[filename]
        # by file matcher:
        for matcher, languages in self._file_matchers.items():
            if matcher(filename):
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
                # by interpreter name
                if interpreter in self._interpreter_names:
                    return self._interpreter_names[interpreter]
                # by interpreter pattern
                for matcher, languages in self._interpreter_matchers.items():
                    if matcher(interpreter):
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
        except IOError:
            languages = {self.LANGUAGE_UNREADABLE}
            return languages
        
    @classmethod
    def language_has_lines_stats(cls, language):
        return not language in cls.NON_TEXT_FILES

    def language_is_binary(self, language):
        return language in self._binary_languages

if __name__ == "__main__":
    language_classifier = LanguageClassifier('languages.ini', 'interpreter.ini')
    import sys
    for arg in sys.argv[1]:
        print(arg, language_classifier.classify(arg))
