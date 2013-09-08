#!/usr/bin/env python3

from .config import Config
from .language_config import LanguageConfig

class StatCodeConfig(Config):
    __sections__ = {
        'config_files': {
            'language_config_file': '',
        }
    }

    def get_language_config(self):
        return LanguageConfig(self['config_files']['language_config_file'])
