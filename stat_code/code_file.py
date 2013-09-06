#!/usr/bin/env python3

import os
import fnmatch
import collections

class FileStats(object):
    def __init__(self, num_lines=0, num_bytes=0):
        self.num_lines = num_lines
        self.num_bytes = num_bytes

    def __add__(self, stats):
        return self.__class__(self.num_lines + stats.num_lines, self.num_bytes + stats.num_bytes)

    def __iadd(self, stats):
        self.num_lines += stats.num_lines
        self.num_bytes += stats.num_bytes

def _invert_dict(d):
    inv_d = collections.defaultdict(set)
    for language, extensions in d.items():
        for extension in extensions:
            inv_d[extension].add(language)
    return inv_d

class File(object):
    LANGUAGE_EXTENSIONS = {
        'C': ('.h', '.hpp', '.c', '.c99'),
        'C++': ('.h', '.hpp', '.c', '.C', '.cxx', '.cpp', '.c++', '.C++'),
        'python': ('.py', ),
        'shell': ('.sh', '.bash', '.csh', '.tcsh'),
        'm4': ('.m4', ),
        'tcl': ('.tcl', ),
        'autoconf': ('.ac', ),
        'automake': ('.am', ),
        'text': ('.txt', ),
        'cmake': ('.cmake', ),
        'make': ('.mk', ),
    }
    LANGUAGE_PATTERNS = {
        'cmake': ('CMake*.txt', ),
        'make': ('Makefile', 'makefile'),
    }
    EXTENSION_LANGUAGES = _invert_dict(LANGUAGE_EXTENSIONS)
    PATTERN_LANGUAGES = _invert_dict(LANGUAGE_PATTERNS)
    
    SHEBANG = '#!'

    INTERPRETERS = {
        'python3':  'python'
    }

    UNCLASSIFIED = '__unclassified__'
    DATA = '__data__'

    def __init__(self, project, filepath, language=None):
        self.project = project
        self.filepath = filepath
        self.language = language
        self.stats = FileStats()
        self.classify()

    def classify(self):
        dirname, filename = os.path.split(self.filepath)
        fileroot, fileext = os.path.splitext(filename)
        try:
            with open(self.filepath, 'r') as filehandle:
                self._languages = None
                if self.language is None:
                    languages = self.guess_languages_filehandle(filehandle, filename, fileext)
                    if len(languages) == 1:
                        self.language = tuple(languages)[0]
                    else:
                        self._languages = languages
                self.stats_filehandle(filehandle)
        except UnicodeDecodeError:
            if self.language is None: 
                self.language = self.DATA
    
    def stats_filehandle(self, filehandle):
        filehandle.seek(0)
        for line in filehandle:
            self.stats += FileStats(1, len(line))

    def post_classify(self):
        if self.language is None:
            self.language = None
            if self._languages:
                for language in self.project.most_common_languages():
                    if language in self._languages:
                        self.language = language
                        break

                if self.language is None:
                    for language in self.project.language_hints():
                        if language in self._languages:
                            self.language = language
                            break


                if self.language is None:
                    self.language = tuple(self._languages)[0]

            if self.language is None:
                self.language = self.UNCLASSIFIED

    @classmethod
    def parse_shebang(cls, filepath):
        with open(filepath, 'r') as f_in:
            return cls.parse_shebang_filehandle(f_in)

    @classmethod
    def parse_shebang_filehandle(cls, filehandle):
        try:
            line = filehandle.readline().rstrip()
            if line.startswith(cls.SHEBANG):
                l = [e.strip() for e in line[len(cls.SHEBANG):].split()]
                if l:
                    if l[0] == '/usr/bin/env' and len(l) > 1:
                        interpreter = l[1]
                    else:
                        interpreter = l[0]
                interpreter = os.path.basename(interpreter)
                language = cls.INTERPRETERS.get(interpreter, interpreter)
                return language
        except UnicodeDecodeError:
            pass
#        finally:
#            input("...")
    
    @classmethod
    def guess_languages(cls, filepath):
        filedir, filename = os.path.split(filepath)
        fileroot, fileext = os.path.splitext(filename)
        with open(filepath, 'r') as filehandle:
            return cls.guess_languages_filehandle(filehandle, filename, fileext)

    @classmethod
    def guess_languages_filehandle(cls, filehandle, filename, fileext):
        language = cls.parse_shebang_filehandle(filehandle)
        if language:
            return {language}
        else:
            languages = cls.EXTENSION_LANGUAGES[fileext]
            if languages:
                return languages
            else:
                for pattern, languages in cls.PATTERN_LANGUAGES.items():
                    if fnmatch.fnmatch(filename, pattern):
                        return languages
                        break
        return {}
        
        
        
