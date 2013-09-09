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

def _ACTION_REMOVE(filename, fileroot, fileext):
    filename = fileroot
    fileroot, fileext = os.path.splitext(filename)
    return filename, fileroot, fileext

class QualifierConfig(Config):

    __actions__ = {
        'remove': _ACTION_REMOVE,
    }
    __defaults__ = {
        'qualifier': '',
        'action': 'remove',
    }

    def get_extension(self, extension):
        section = self[extension]
        qualifier = section['qualifier']
        action = self.__actions__[section['action']]
        return qualifier, action
        
