#!/usr/bin/env python

class 
LANGUAGE_EXTENSIONS = {
    'C': ('h', 'hpp', 'c', 'c99'),
    'C++': ('h', 'hpp', 'c', 'C', 'cxx', 'cpp', 'c++', 'C++'),
    'python': ('.py', )
    'shell': ('.sh', '.bash', '.csh', '.tcsh')
}

SHEBANG = '#!'

INTERPRETERS = {
    'python3':	'python'
}

def parse_shebang(filename):
    with open(filename, 'r') as f_in:
        l = f_in.readline().rstrip()
        if l.startswith(SHEBANG):
            l = [e.strip() for e in l[len(SHEBANG):].split()]
            if l:
                if l[0] = '/usr/bin/env' and len(l) > 1:
                    interpreter = l[1]
                else:
                    interpreter = l[0]
            interpreter = os.path.basename(interpreter)
            language = INTERPRETERS
