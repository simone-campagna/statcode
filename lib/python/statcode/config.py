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

import configparser

class Config(configparser.ConfigParser):
    __sections__ = {}
    __defaults__ = {}
    def __init__(self, filename=None):
        super().__init__(self.__defaults__)
        self.filename = filename
        self.load()
        self.set_defaults()

    def set_defaults(self):
        lst = [(self, self.__sections__)]
        while lst:
            lst_copy = lst[:]
            del lst[:]
            for section, defaults in lst_copy:
                for key, value in defaults.items():
                    if isinstance(value, dict):
                        if not key in section:
                            section[key] = {}
                        lst.append((section[key], value))
                    else:
                        if not key in section:
                            section[key] = str(value)

    def load(self):
        if self.filename:
            with open(self.filename, 'r') as f_in:
                self.read_file(f_in, self.filename)

    def store(self):
        if self.filename:
            with open(self.filename, 'w') as f_out:
                self.write(f_out)

    @classmethod
    def list_to_string(cls, lst):
        return ':'.join(lst)

    @classmethod
    def string_to_list(cls, s):
        s = s.strip()
        if s:
            return s.split(':')
        else:
            return []

    @classmethod
    def make_list(cls, *tokens):
        return cls.list_to_string(tokens)
