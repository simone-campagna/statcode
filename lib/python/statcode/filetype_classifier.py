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
from .filetype_config import FileTypeConfig

class FileTypeClassifier(object):
    SHEBANG = '#!'
    FILETYPE_DATA = '{data}'
    FILETYPE_BROKEN_LINK = '{broken-link}'
    FILETYPE_NO_FILE = '{no-file}'
    FILETYPE_UNREADABLE = '{unreadable}'
    FILETYPE_UNCLASSIFIED = '{unclassified}'
    NO_FILETYPE_FILES = {FILETYPE_DATA, FILETYPE_BROKEN_LINK, FILETYPE_NO_FILE, FILETYPE_UNCLASSIFIED, FILETYPE_UNREADABLE}
    BINARY_FILES = {FILETYPE_DATA}
    NON_EXISTENT_FILES = {FILETYPE_BROKEN_LINK, FILETYPE_NO_FILE, FILETYPE_UNREADABLE}
    DEFAULT_CATEGORY = FileTypeConfig.DEFAULT_CATEGORY
    def __init__(self, filetype_config, qualifier_config):
        self._file_extensions = collections.defaultdict(set)
        self._file_extension_names = collections.defaultdict(set)
        self._file_extension_matchers = collections.defaultdict(set)
        self._file_names = collections.defaultdict(set)
        self._file_matchers = collections.defaultdict(set)
        self._interpreter_names = collections.defaultdict(set)
        self._interpreter_matchers = collections.defaultdict(set)
        self._binary_filetypes = set()
        self._filetype_category = collections.defaultdict(lambda : self.DEFAULT_CATEGORY)
        self._keyword_res = collections.defaultdict(set)

        # from filetype_config
        for filetype in filetype_config.sections():
            section = filetype_config[filetype]
            self._filetype_category[filetype] = section['category']
            if filetype_config.string_to_bool(section['binary']):
                self._binary_filetypes.add(filetype)
            for extension in filetype_config.string_to_list(section['file_extensions']):
                self._file_extensions[os.path.extsep + extension].add(filetype)
            for pattern in filetype_config.string_to_list(section['file_patterns']):
                extensions = set()
                patternroot, patternext = os.path.splitext(pattern)
                for extension in self._file_extensions:
                    if fnmatch.fnmatch(extension, patternext):
                        extensions.add(extension)
                if patternutils.is_regular_expression(pattern):
                    matcher = patternutils.get_matcher(pattern)
                    self._file_matchers[matcher].add(filetype)
                    for extension in extensions:
                        self._file_extension_matchers[extension].add(matcher)
                else:
                    self._file_names[pattern].add(filetype)
                    for extension in extensions:
                        self._file_extension_names[extension].add(pattern)
            
            for pattern in filetype_config.string_to_list(section['interpreter_patterns']):
                if patternutils.is_regular_expression(pattern):
                    matcher = patternutils.get_matcher(pattern)
                    self._interpreter_matchers[matcher].add(filetype)
                else:
                    self._interpreter_names[pattern].add(filetype)

            keyword_res = self._keyword_res[filetype]
            for keyword in filetype_config.string_to_list(section['keywords']):
                keyword_re = self._get_keyword_re(keyword)
                keyword_res.add(keyword_re)

        # from qualifier_config
        self._qualifier = {}
        for extension in qualifier_config.sections():
            self._qualifier[os.path.extsep + extension] = qualifier_config.get_extension(extension)
 
    def _get_keyword_re(self, keyword):
        return re.compile("(?<!\w)" + re.escape(keyword) + "(?!\w)")

    def get_category(self, filetype):
        return self._filetype_category[filetype]

    def classify(self, filepath, filename=None):
        filetypes = None
        if not os.path.exists(os.path.realpath(filepath)):
            if os.path.lexists(filepath):
                return [], {self.FILETYPE_BROKEN_LINK}
            else:
                return [], {self.FILETYPE_NO_FILE}

        if filename is None:
            filename = os.path.basename(filepath)
   
        fileroot, fileext = os.path.splitext(filename)
        qualifiers, filetypes = self.classify_by_filename(filename, fileroot, fileext)

        if filetypes is None:
            try:
                with open(filepath, 'r') as filehandle:
                    filetypes = self.classify_by_shebang(filehandle, filepath, filename)
            except UnicodeDecodeError:
                filetypes = {self.FILETYPE_DATA}
            except IOError:
                filetypes = {self.FILETYPE_UNREADABLE}

        return qualifiers, filetypes

    def classify_by_filename(self, filename, fileroot, fileext):
        qualifiers = []

        # qualifier, by extension
        qualifier = None
        if fileext in self._qualifier:
            qualifier, action = self._qualifier[fileext]
            qualifiers.append(qualifier)
            filename, fileroot, fileext = action(filename, fileroot, fileext)
            next_qualifiers, filetypes = self.classify_by_filename(filename, fileroot, fileext)
            qualifiers.extend(next_qualifiers)
        else:
            filetypes = self.classify_filetypes_by_filename(filename, fileroot, fileext)
        return qualifiers, filetypes

    def classify_filetypes_by_filename(self, filename, fileroot, fileext):
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
        for matcher, filetypes in self._file_matchers.items():
            if matcher(filename):
                return filetypes
        return None

    def classify_by_content(self, restrict_filetypes, filepath):
        try:
            with open(filepath, 'r') as filehandle:
                return self.classify_by_content_filehandle(restrict_filetypes, filepath, filehandle)
        except UnicodeDecodeError:
            return self.FILETYPE_DATA
        except IOError:
            return self.FILETYPE_UNREADABLE

    def classify_by_content_filehandle(self, restrict_filetypes, filepath, filehandle):
        if len(restrict_filetypes) == 1:
            return {next(iter(restrict_filetypes))}

        scores = collections.defaultdict(lambda : 0)
        min_lines = 100
        max_ratio = 0.3
        min_score = 50
        num_lines = 0
        for line in filehandle:
            for filetype in restrict_filetypes:
                score = 0
                for keyword_re in self._keyword_res[filetype]:
                    for m in keyword_re.finditer(line):
                        score += 1
                scores[filetype] += score
            num_lines += 1
            if num_lines > min_lines:
                l = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                first, first_score = l[0]
                second, second_score = l[1]
                if first_score:
                    if second_score:
                        if second_score / first_score < max_ratio:
                            return {first}
                    else:
                        if first_score > min_score:
                            return {first}
        l = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        first, first_score = l[0]
        result = set()
        for filetype, score in l:
            if score != first_score:
                break
            result.add(filetype)
        return result

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
                for matcher, filetypes in self._interpreter_matchers.items():
                    if matcher(interpreter):
                        return filetypes
                        break
                else:
                    filetypes = {interpreter}
                    return filetypes
            else:
                # no shebang
                return None
        except UnicodeDecodeError:
            filetypes = {self.FILETYPE_DATA}
            return filetypes
        except IOError:
            filetypes = {self.FILETYPE_UNREADABLE}
            return filetypes
        
    def filetype_is_binary(self, filetype):
        return filetype in self._binary_filetypes

if __name__ == "__main__":
    filetype_classifier = FileTypeClassifier('filetypes.ini', 'interpreter.ini')
    import sys
    for arg in sys.argv[1]:
        print(arg, filetype_classifier.classify(arg))
