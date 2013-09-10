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

import re
import fnmatch

SPECIAL_SYMBOLS = set('*[]!?')

NEGATE_PATTERN = '!'

_CACHED = {}

def special_symbols(pattern):
    return SPECIAL_SYMBOLS.intersection(pattern)

def contains_special_symbols(pattern):
    return bool(special_symbols(pattern))

is_regular_expression = contains_special_symbols

def get_matcher(pattern):
    if not pattern in _CACHED:
        _CACHED[pattern] = re.compile(fnmatch.translate(pattern)).match
    return _CACHED[pattern]

def filter_patterns(patterns):
    matchers = set()
    names = set()
    for pattern in patterns:
        if is_regular_expression(pattern):
            matchers.add(get_matcher(pattern))
        else:
            names.add(pattern)
    return names, matchers

def match_names_or_matchers(names, matchers, value):
    if value in names:
        return True
    for matcher in matchers:
        if matcher(value):
            return True
    return False
        
def get_signed_pattern(pattern):
    if pattern and pattern[0] == NEGATE_PATTERN:
        sign = NEGATE_PATTERN
        pattern = pattern[1:]
    else:
        sign = ''
    return sign, pattern

def apply_signed_patterns(items, signed_patterns):
    all_items = set(items)
    selected_items = None
    for signed_pattern in signed_patterns:
        sign, pattern = get_signed_pattern(signed_pattern)
        if sign == NEGATE_PATTERN:
            if selected_items is None:
                selected_items = set(all_items)
            selected_items.difference_update(fnmatch.filter(selected_items, pattern))
        else:
            if selected_items is None:
                selected_items = set()
            selected_items.update(fnmatch.filter(all_items, pattern))
    if selected_items is None:
        selected_items = items
    return selected_items

