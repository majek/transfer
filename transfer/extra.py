from __future__ import print_function
import inspect
import sys
import os
import glob
import re
import os.path

def FATAL(msg=""):
    frame,filename,line_number,function_name,lines,index=\
        inspect.getouterframes(inspect.currentframe())[1]

    print("[-] PROGRAM ABORT : %s" % (msg,), file=sys.stderr)
    print("\t Location : %s() %s:%i" % (function_name, os.path.basename(filename), line_number,),
          file=sys.stderr)
    sys.exit(1)


def read_directory(dirname):
    if not os.path.isdir(dirname):
        FATAL("%r is not a directory" % (dirname,))

    count = 0
    for fullname in glob.glob(os.path.join(dirname, '*.tif')):
        basename = os.path.basename(fullname)
        filename, ext = os.path.splitext(basename)
        m = re.match("(?P<name>.*)-source$", filename)
        if not m:
            continue
        name = m.groupdict()['name']

        m = re.match("^(?P<prefix>.*)-source.tif$", fullname)
        prefix = m.groupdict()['prefix']
        yield (name, prefix)
        count += 1
    if not count:
        FATAL("%r doesn't contain any '*-source.tif' files!" % (dirname,))
