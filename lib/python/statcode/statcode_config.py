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

class StatCodeConfig(Config):
    __sections__ = {
        'config_files': {
            'language_config_file': '',
        }
    }

    def get_language_config(self):
        language_config_file = self['config_files']['language_config_file']
        if not os.path.isabs(language_config_file):
            language_config_file = os.path.join(os.path.dirname(self.filename), language_config_file)
        if not os.path.exists(language_config_file):
            raise ValueError("language config file {!r} does not exists".format(language_config_file))
        return LanguageConfig(language_config_file)
