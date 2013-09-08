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
import re
import sys
import glob
import getpass
import tempfile

#dirname = os.path.dirname(os.path.abspath(sys.argv[0]))
#py_dirname = os.path.join(dirname, "lib", "python")
#sys.path.append(py_dirname)

from distutils.core import setup
from distutils import log
from distutils.command.install_data import install_data
from distutils.command.install_scripts import install_scripts
from distutils.cmd import Command

class pre_command(object):
    def run(self):
        install_cmd = self.get_finalized_command('install')
        self.install_base = os.path.normpath(os.path.abspath(getattr(install_cmd, 'install_base')))
        self.admin_user = getpass.getuser()
        return super().run()

class subst_command(Command):
    def _init(self):
        if not hasattr(self, 'r_list'):
            v_dict = {
                'STATCODE_HOME_DIR':        self.install_base,
            }
            self.r_list = []
            for key, val in v_dict.items():
                self.r_list.append((re.compile(r"@{0}@".format(key)), val))

    def transform_file(self, infile, outfile):
        self._init()
        log.info("substituting {0} -> {1}...".format(infile, outfile))
        with open(outfile, "w") as f_out, open(infile, "r") as f_in:
            source = f_in.read()
            for regular_expression, substitution in self.r_list:
                source = regular_expression.sub(substitution, source)
                #print("___>", substitution)
            f_out.write(source)
        
    def copy_file(self, infile, outfile, preserve_mode=1, preserve_times=1, link=None, level=1):
        with tempfile.TemporaryDirectory(prefix=os.path.basename(infile)) as tmpdir:
            tmpfile = os.path.join(tmpdir, os.path.basename(infile))
            self.transform_file(infile, tmpfile)
            result = super().copy_file(tmpfile, outfile, preserve_mode=preserve_mode, preserve_times=preserve_times, link=link, level=level)
        return result

    def copy_tree(self, infile, outfile, preserve_mode=1, preserve_times=1,
                  preserve_symlinks=0, level=1):
        with tempfile.TemporaryDirectory(prefix=os.path.basename(infile)) as tmpdir:
            for dirpath, dirnames, filenames in os.walk(infile):
                rdir = os.path.relpath(dirpath, infile)
                tmpd = os.path.join(tmpdir, rdir)
                if not os.path.isdir(tmpd):
                    os.makedirs(tmpd)
                for filename in filenames:
                    in_filename = os.path.join(dirpath, filename)
                    out_filename = os.path.join(tmpd, filename)
                    self.transform_file(in_filename, out_filename)
            result = super().copy_tree(tmpdir, outfile, preserve_mode=preserve_mode, preserve_times=preserve_times, preserve_symlinks=preserve_symlinks, level=level)
        return result

class subst_install_data(pre_command, install_data, subst_command):
    pass

class subst_install_scripts(pre_command, install_scripts, subst_command):
    pass

setup(
    name = "statcode",
    version = "0.1",
    requires = [],
    description = "Show statistics about source code",
    author = "Simone Campagna",
    author_email = "simone.campagna@tiscali.it",
    url="https://github.com/simone-campagna/statcode",
    packages = ["statcode"],
    package_dir = {"statcode": "lib/python/statcode"},
    scripts = [
	'bin/statcode',
    ],
    data_files = [
        ('etc/statcode', glob.glob('etc/statcode/*.ini')),
    ],
    cmdclass = {
        'install_data': subst_install_data,
        'install_scripts': subst_install_scripts,
    },
)

