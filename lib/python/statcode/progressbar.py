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

import sys

class OverridingStream(object):
    def __init__(self, stream=None):
        self.stream = stream
        self._last_line_length = None
        
    def write(self, line):
        if self._last_line_length is None:
            self.stream.write("{}".format(line))
        else:
            self.stream.write("\r{}\r{}".format(" " * self._last_line_length, line))
        self.stream.flush()
        self._last_line_length = len(line)

class ProgressBar(object):
    PRE = '['
    POST = ']'
    BLOCK = '#'
    EMPTY = ' '
    MESSAGE = "{current_fraction:.1%} "
    def __init__(self,
                    maximum=100.0,
                    *,
                    length=70,
                    current=0.0,
                    increment=1.0,
                    message=None,
                    pre=None,
                    post=None,
                    block=None,
                    empty=None,
                    stream=None,
                    **render_args):
        self.maximum = maximum
        self.current = current
        self.increment = increment
        self.length = length
        if message is None:
            message = self.MESSAGE
        self.message = message
        if pre is None:
            pre = self.PRE
        self.pre = pre
        if post is None:
            post = self.POST
        self.post = post
        if block is None:
            block = self.BLOCK
        self.block = block
        if empty is None:
            empty = self.EMPTY
        self.empty = empty
        if stream is None:
            stream = OverridingStream(sys.stdout)
        self.stream = stream
        self.render_args = render_args
             
    def get_line(self,
                *,
                current=None,
                increment=None,
                maximum=None,
                message=None,
                **render_args):
        if maximum is not None:
            self.maximum = maximum
        if message is not None:
            self.message = message
        previous = self.current
        if current is None:
            if increment is None:
                increment = self.increment
            current = self.current + increment
        self.current = current
        if self.current > self.maximum:
            self.maximum = self.current
        increment = self.current - previous

        current_fraction = self.current / self.maximum
        missing_fraction = 1.0 - current_fraction
        format_d = dict(
            current_fraction=current_fraction,
            missing_fraction=missing_fraction,
            current=self.current,
            maximum=self.maximum,
            increment=increment,
            missing=self.maximum - self.current)
        format_d.update(self.render_args)
        format_d.update(render_args)
        message = self.message.format(**format_d)
        pre = self.pre.format(**format_d)
        post = self.post.format(**format_d)

        fixed_length = len(message) + len(pre) + len(post)
        variable_length = self.length - fixed_length
        if self.maximum == 0.0:
            block_fraction = 0
        else:
            block_fraction = self.current / self.maximum
        block_length = int(round(block_fraction * variable_length))
        empty_length = variable_length - block_length
        block_num = (block_length + len(self.block) - 1) // len(self.block)
        block = (self.block * block_num)[:block_length]
        empty_num = (empty_length + len(self.empty) - 1) // len(self.empty)
        empty = (self.empty * empty_num)[:empty_length]

        line = message + pre + block + empty + post
        #assert len(line) == self.length
        return line

    def render(self, **n_args):
        self.stream.write(self.get_line(**n_args))

    def initialize(self):
        self.render(current=self.current)

    def finalize(self):
        self.stream.write("")

    def sub_progress_bar(self, intervals, **render_args):
        sub_current = self.current
        sub_increment = self.increment / intervals
        args = self.render_args.copy()
        args.update(render_args)
        return self.__class__(
                    length=self.length,
                    maximum=self.maximum,
                    current=sub_current,
                    increment=sub_increment,
                    message=self.message,
                    pre=self.pre,
                    post=self.post,
                    block=self.block,
                    empty=self.empty,
                    stream=self.stream,
                    **args)

if __name__ == "__main__":
    import time
    progress_bar = ProgressBar(increment=10.0, post=" {current}")
    print("inizio...")
    progress_bar.initialize()
    time.sleep(0.5)
    progress_bar.render()
    time.sleep(0.5)
    progress_bar.render(current=12.5)
    time.sleep(0.5)
    progress_bar.render(increment=55.6)
    time.sleep(0.5)
    progress_bar.render()
    time.sleep(0.5)
    progress_bar.render()
    time.sleep(0.5)
    progress_bar.render()
    time.sleep(0.5)
    progress_bar.render()
    time.sleep(0.5)
    progress_bar.render()
    time.sleep(0.5)
    progress_bar.finalize()
    print("finito")
