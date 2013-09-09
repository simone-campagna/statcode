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
from .language_config import LanguageConfig
from .directory_config import DirectoryConfig

class StatCodeConfig(Config):
    __sections__ = {
        'config_files': {
            'language_config_files': '',
            'directory_config_files': '',
        }
    }

    def _absolute_config_files(self, key):
        filenames = []
        for filename in self.string_to_list(self['config_files'][key]):
            filenames.append(self.absolute_filename(filename))
        return filenames

    def update(self, cnfg):
        language_config_files = self._absolute_config_files('language_config_files') + \
                                cnfg._absolute_config_files('language_config_files')
        self['config_files']['language_config_files'] = self.list_to_string(language_config_files)
        directory_config_files = self._absolute_config_files('directory_config_files') + \
                                 cnfg._absolute_config_files('directory_config_files')
        self['config_files']['directory_config_files'] = self.list_to_string(directory_config_files)

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
            
    def get_language_config(self):
        language_config = LanguageConfig()
        for language_config_file in self.string_to_list(self['config_files']['language_config_files']):
            if not os.path.isabs(language_config_file):
                language_config_file = os.path.join(os.path.dirname(self.filename), language_config_file)
            if not os.path.exists(language_config_file):
                raise ValueError("language config file {!r} does not exists".format(language_config_file))
            language_config.update(LanguageConfig(language_config_file))
        return language_config

    def get_directory_config(self):
        directory_config = DirectoryConfig()
        for directory_config_file in self.string_to_list(self['config_files']['directory_config_files']):
            if not os.path.isabs(directory_config_file):
                directory_config_file = os.path.join(os.path.dirname(self.filename), directory_config_file)
            if not os.path.exists(directory_config_file):
                raise ValueError("directory config file {!r} does not exists".format(directory_config_file))
            directory_config.update(LanguageConfig(directory_config_file))
        return directory_config
