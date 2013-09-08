#!/usr/bin/env python3

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

