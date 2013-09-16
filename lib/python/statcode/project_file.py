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
from .filetype_classifier import FileTypeClassifier

class ProjectFile(object):
    def __init__(self, filepath, project_dir, filetype=None):
        self.project_dir = project_dir
        self.filetype_classifier = project_dir.project.filetype_classifier
        self.filepath = filepath
        self._filetypes = None
        self.qualifiers = None
        self.filetype = filetype
        self.file_stats = None

    def pre_classify(self):
        qualifiers, self._filetypes = self.filetype_classifier.classify(self.filepath)
        if qualifiers:
            self.qualifiers = ";".join(qualifiers) + '-'
        if self._filetypes is not None:
            if len(self._filetypes) == 0:
                self.filetype = FileTypeClassifier.FILETYPE_UNCLASSIFIED
            elif len(self._filetypes) == 1:
                self.filetype = next(iter(self._filetypes))
        #print("PRE", self.filepath, self._filetypes, self.filetype)

    def post_classify(self):
#        if self.filepath.endswith(".h"):
#            print("***", self.filepath, self.filetype, self._filetypes)
        if self.filetype is None:
            if self._filetypes is None:
                self.filetype = FileTypeClassifier.FILETYPE_UNCLASSIFIED
            else:
                self._filetypes = self.filetype_classifier.classify_by_content(self._filetypes, self.filepath)
                if len(self._filetypes) == 1:
                    self.filetype = next(iter(self._filetypes))
                else:
                    project_dir = self.project_dir
                    while project_dir:
                        for filetype in project_dir.most_common_filetypes():
                            assert not filetype in FileTypeClassifier.NO_FILETYPE_FILES
                            if filetype in self._filetypes:
                                self.filetype = filetype
                                #print("HERE A: ", self.filepath, self._filetypes, self.filetype, project_dir.dirpath)
                                break
                        else:
                            project_dir = project_dir.parent
                            continue
                        break
                    else:
                        #self.filetype = next(iter(self._filetypes))
                        self.filetype = next(iter(self._filetypes))
                        #print("HERE Z: ", self.filepath, self._filetypes, self.filetype)

        # stats
        if self.filetype in FileTypeClassifier.NON_EXISTENT_FILES:
            self.file_stats = FileStats()
        else:
            block_size = self.project_dir.project.block_size
            num_lines = 0
            num_bytes = 0
            newline = b'\n'
            try:
                with open(self.filepath, 'rb') as filehandle:
                    last_block = None
                    while True:
                        block = filehandle.read(block_size)
                        if not block:
                            break
                        last_block = block
                        num_bytes += len(block)
                        num_lines += block.count(newline)
                    if last_block and last_block[-1] != newline:
                        num_lines += 1
                    self.file_stats = FileStats(lines=num_lines, bytes=num_bytes)
            except (OSError, IOError) as e:
                self.filetype = FileTypeClassifier.FILETYPE_UNREADABLE
                self.file_stats = FileStats()
                try:
                    self.file_stats.bytes += os.stat(self.filepath).st_size
                except:
                    pass
            #if self.filetype_classifier.filetype_is_binary(self.filetype):
            #    self.file_stats = FileStats(bytes=os.stat(self.filepath).st_size)
            #else:
            #    try:
            #        with open(self.filepath, 'r') as filehandle:
            #            num_lines = 0
            #            num_bytes = 0
            #            for line in filehandle:
            #                num_bytes += len(line)
            #                num_lines += 1
            #            self.file_stats = FileStats(lines=num_lines, bytes=num_bytes)
            #    except UnicodeDecodeError as e:
            #        self.filetype = FileTypeClassifier.FILETYPE_DATA
            #        self.file_stats = FileStats(bytes=os.stat(self.filepath).st_size)
        #print("POST", self.filepath, self._filetypes, self.filetype)
        
        
