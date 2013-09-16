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
    def __init__(self, filetype_config, qualifier_config, parameters):
        self._parameters = dict(parameters)
        self._file_extensions = collections.defaultdict(set)
        self._file_extension_names = collections.defaultdict(set)
        self._file_extension_matchers = collections.defaultdict(set)
        self._file_names = collections.defaultdict(set)
        self._file_matchers = collections.defaultdict(set)
        self._interpreter_names = collections.defaultdict(set)
        self._interpreter_matchers = collections.defaultdict(set)
        self._binary_filetypes = set()
        self._filetype_category = collections.defaultdict(lambda : self.DEFAULT_CATEGORY)
        self._filetype_keywords = {}
        self._keyword_res = {}
        self._keyword_filetypes = collections.defaultdict(set)

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

            keywords = set()
            for keyword in filetype_config.string_to_list(section['keywords']):
                self._keyword_filetypes[keyword].add(filetype)
                keywords.add(keyword)
                if not keyword in self._keyword_res:
                    keyword_re = re.compile("(?<!\w)" + re.escape(keyword) + "(?!\w)")
                    self._keyword_res[keyword] = keyword_re
            self._filetype_keywords[filetype] = keywords

        # from qualifier_config
        self._qualifier = {}
        for extension in qualifier_config.sections():
            self._qualifier[os.path.extsep + extension] = qualifier_config.get_extension(extension)
 

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

    def _sorted_filetype_scores(self, filetypes, keyword_scores):
        filetype_scores = []
        for filetype in filetypes:
            filetype_score = 0
            for keyword in self._filetype_keywords[filetype]:
                filetype_score += keyword_scores[keyword]
            filetype_scores.append((filetype, filetype_score))
        filetype_scores.sort(key=lambda x: x[1], reverse=True)
        return filetype_scores
                
    def classify_by_content_filehandle(self, restrict_filetypes, filepath, filehandle):
        if len(restrict_filetypes) == 1:
            return {next(iter(restrict_filetypes))}

        min_lines = self._parameters['min_lines']
        max_lines = self._parameters['max_lines']
        max_ratio = self._parameters['max_ratio']
        score_ratio = self._parameters['score_ratio']
        block_lines = self._parameters['block_lines']
        num_lines = 0
        keywords = set()
        keyword_filetypes = {}
        filetypes = set()
        for filetype in restrict_filetypes:
            filetype_keywords = self._filetype_keywords[filetype]
            if filetype_keywords:
                filetypes.add(filetype)
                keywords.update(filetype_keywords)
        for keyword in keywords:
            keyword_filetypes[keyword] = self._keyword_filetypes[keyword].intersection(filetypes)
        keyword_res = self._keyword_res
        keyword_scores = dict((keyword, 0) for keyword in keywords)
        non_keyword_filetypes = set(restrict_filetypes).difference(filetypes)

        for line in filehandle:
            for keyword in keywords:
                keyword_re = keyword_res[keyword]
                score = 0
                for m in keyword_re.finditer(line):
                    score += 1
                keyword_scores[keyword] += 1
            num_lines += 1
            if num_lines > min_lines and (num_lines % block_lines == 0):
                filetype_scores = self._sorted_filetype_scores(filetypes, keyword_scores)
                first, first_score = filetype_scores[0]
                second, second_score = filetype_scores[1]
                if first_score:
                    if second_score:
                        #print("!", filetype_scores, first_score, second_score, second_score / first_score)
                        if second_score / first_score < max_ratio:
                            #print("A", filepath, repr(first), first_score, repr(second), second_score)
                            return {first}
                    else:
                        if first_score > num_lines * score_ratio:
                            #print("B", filepath, repr(first), first_score, repr(second), second_score)
                            return {first}
            if num_lines > max_lines:
                break
        filetype_scores = self._sorted_filetype_scores(filetypes, keyword_scores)
        first, first_score = filetype_scores[0]
        if first_score >= num_lines * score_ratio:
            result = set()
            for filetype, score in filetype_scores:
                if score != first_score:
                    break
                result.add(filetype)
            #print("C", filepath, repr(first), first_score, num_lines)
            return result
        else:
            #print("D", filepath, repr(first), first_score, num_lines)
            return non_keyword_filetypes

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
