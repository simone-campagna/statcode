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

from .config import Config
from .filetype_config import FileTypeConfig
from .directory_config import DirectoryConfig
from .qualifier_config import QualifierConfig

class StatCodeConfig(Config):
    __key_class__ = {
            'filetype_config_files': FileTypeConfig,
            'directory_config_files': DirectoryConfig,
            'qualifier_config_files': QualifierConfig,
    }
    __keys__ = list(__key_class__.keys())
    __sections__ = {
        'config_files': dict((key, '') for key in __keys__),
        'parameters': {
            'min_lines': 30,
            'max_lines': 500,
            'max_ratio': 1.0,
            'score_ratio': 0.1,
            'block_lines': 20,
        }
    }

    def _absolute_config_files(self, key):
        filenames = []
        for filename in self.string_to_list(self['config_files'][key]):
            filenames.append(self.absolute_filename(filename))
        return filenames

    def update(self, cnfg):
        for key in self.__keys__:
            self.update_key(key, cnfg)

    def update_key(self, key, cnfg):
        config_files = self._absolute_config_files(key) + \
                       cnfg._absolute_config_files(key)
        self['config_files'][key] = self.list_to_string(config_files)


    def _absolute_files(self, filenames):
        if not self.filename:
            return
        basename = os.path.basename(self.filename)
        abs_filenames = []
        for filename in filenames:
            if not os.path.isabs(filename):
                filename = os.path.join(os.path.dirname(self.filename), filename)
            if not os.path.exists(filename):
                raise ValueError("config file {!r} does not exists".format(filename))
            abs_filenames.append(filename)
        return abs_filenames

    def get_key_config(self, key):
        key_config_class = self.__key_class__[key]
        key_config = key_config_class()
        for config_file in self.string_to_list(self['config_files'][key]):
            config_file = self.absolute_filename(config_file)
            key_config.update(key_config_class(config_file))
        return key_config
            
    def get_filetype_config(self):
        return self.get_key_config('filetype_config_files')

    def get_directory_config(self):
        return self.get_key_config('directory_config_files')

    def get_qualifier_config(self):
        return self.get_key_config('qualifier_config_files')
