from __future__ import print_function
import itertools
import glob
import sys
import os
import re
import array

from . import extra as x
from . import img
from . import network


class InputFile(object):
    input_filename = None
    output_filename = None
    results = None

    def __init__(self, name):
        self.name = name

    def attempt_filename(self, v=''):
        return "%s-attempt%s.png" % (self.name,v)

    def load_source(self):
        self.layers = img.load_source(self.input_filename)

    def load_results(self):
        self.results = img.decipher_result_file(self.output_filename)
        self.results_layer = img.results_to_layer(self.layers[0].size,
                                                  self.results, multiplier=0.9)

    def save_rectangle(self):
        img.save_rectangle(self.layers, self.results,
                           self.attempt_filename("-rect"))

    def save_results_layer(self):
        img.save_results_layer(self.layers, self.results_layer,
                               self.attempt_filename("-raw"))

    def save_counted_results(self):
        img.save_results_layer(self.layers, self.counted_result,
                               self.attempt_filename("-network"))


def load_files():
    inputs = {}

    for filename in map(os.path.basename,
                        itertools.chain(glob.glob("./*tif"),
                                    glob.glob("./*tiff"))):
        fname, ext = os.path.splitext(filename)
        a = re.match("(?P<name>.*)-attempt$", fname)
        if a:
            continue
        m = re.match("(?P<name>.*)[-_]out(put)?$", fname)
        if m:
            name = m.groupdict()['name']
        else:
            name = fname

        if name not in inputs:
            inputs[name] = InputFile(name)

        if m:
            inputs[name].output_filename = filename
        else:
            inputs[name].input_filename = filename

    for i in inputs.itervalues():
        if not i.input_filename:
            x.FATAL("stray output file %r" % (i.output_filename,))
    inputs = sorted(inputs.values(), key=lambda i:i.name)

    return inputs


if __name__ == "__main__":
    if sys.argv[1:]:
        newdir = sys.argv[1]
        print("[+] Changing directory to %r" % (newdir,))
        os.chdir(newdir)

    WSIZE=8
    net = network.Network(WSIZE*WSIZE*2)

    files = load_files()
    print("[.] Loading files:")
    for i in files:
        print("[.] %r --> %r" % (i.input_filename, i.output_filename))
        i.load_source()

    print("[ ] Generating training data")
    for i in files:
        print("[.] %r --> %r" % (i.input_filename, i.output_filename))
        if i.output_filename:
            i.load_results()
            i.save_results_layer()
            i.save_rectangle()
            w1 = i.layers[0].windows_fun(WSIZE)
            w2 = i.layers[1].windows_fun(WSIZE)

            for c in xrange(i.layers[0].size[0] * i.layers[0].size[1]):
                result = i.results_layer.a[c]
                if result != 0.0 or c % (37*6) == 0:
                    net.addSample(c, itertools.chain(w1(c).a, w2(c).a), result)
                    #print("#%i r=%f i=%r" % (c, i.results_layer.a[c], list(window.a[0:5])))
    print("[ ] Training %i samples..." % (len(net.ds),))
    td = net.train()
    print("[ ] Done in %.3f seconds" % (td,))

        # x = window.to_image()
        # x.save('a.png')
        # os.exit(1)
        #i.save_rectangle()
        #i.save_results_layer()
        #r = i.layers[0].bigger((10, 10)).to_image()

    for i in files:
        print("[.] %r --> %r" % (i.input_filename, i.output_filename))
        max_c = i.layers[0].size[0] * i.layers[0].size[1]
        try:
            w1 = i.layers[0].windows_fun(WSIZE)
            w2 = i.layers[1].windows_fun(WSIZE)
            i.counted_result = img.Layer(i.layers[0].size)

            print("[ ] trained pixels")
            for c in net.c_numbers:
                r = net.run(itertools.chain(w1(c).a, w2(c).a))
                #print("%s  %f~%f" % (c, i.results_layer.a[c], r))
                i.counted_result.a[c] = r
            print("[ ] all pixels")
            for c in xrange(0, max_c, 7):
                i.counted_result.a[c] = net.run(itertools.chain(w1(c).a, w2(c).a))
                if c % 15000 == 0:
                    print('%.2i %%' % ((float(c) / max_c)*100.))
                    i.counted_result.a[c+1] = 1.0
                    i.counted_result.a = array.array('f', (min(1., max(0.,v))
                                                           for v in i.counted_result.a))
                    i.save_counted_results()

        except KeyboardInterrupt:
            pass
        print("[ ] Saving")
        i.counted_result.a[c] = 1.0
        i.counted_result.a = array.array('f', (min(1., max(0.,v))
                                               for v in i.counted_result.a))
        i.save_counted_results()
