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

from .config import Config

class LanguageConfig(Config):
    __defaults__ = {
        'file_extensions': '',
        'file_patterns': '',
        'interpreter_patterns': '',
    }

if __name__ == "__main__":
    import sys
    c = LanguageConfig()
    c.write(sys.stdout)
    c['C++'] = {
        'file_extensions': LanguageConfig.make_list('.h', '.hpp', '.C', '.cxx', '.cpp', '.c++', '.C++'),
    }
    c['cmake'] = {
        'file_extensions': LanguageConfig.make_list(".cmake"),
        'file_patterns': LanguageConfig.make_list("Cmake*.txt"),
    }
    c.write(sys.stdout)
    print(c['C++']['file_patterns'])
