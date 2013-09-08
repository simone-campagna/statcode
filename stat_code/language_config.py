#!/usr/bin/env python3

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
