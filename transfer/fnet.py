from pyfann import libfann
import os
import tempfile
import time
import signal
import math
import cPickle as pickle
import array
import random

from . import const
from . import extra as x

class Network(object):
    window = None
    size = None
    ratio = None
    multiplier = None
    type = None

    def __init__(self, filename):
        self.filename = filename

        (fd, self.dataset_filename) = tempfile.mkstemp(
            suffix=os.path.basename(filename) + ".data")
        os.close(fd)

        self.samples = []
        self.max_iterations = 16

    def preset(self, window, ratio, size, multiplier, etype):
        self.window = window
        self.ratio = ratio
        self.size = size
        self.multiplier = multiplier
        self.type = etype

    def addSample(self, data, result):
        self.samples.append( (data, result) )

    def new(self):
        self.net = libfann.neural_net()
        num_input = self.window*self.window*2+1
        num_hidden = self.window*self.window*2
        num_output = 1

        self.net.create_standard_array((num_input, num_hidden, self.window, num_output))
        self.net.randomize_weights(-1., 1.)
        self._set_funs()

    def _set_funs(self):
        #self.net.set_activation_function_input(libfann.SIGMOID)
        self.net.set_activation_function_hidden(libfann.SIGMOID)
        self.net.set_activation_function_output(libfann.SIGMOID)

    def train(self, samples_chunk, desired_error=0.0001):
        with open(self.dataset_filename, 'wb') as f:
            f.write("%i %i %i\n" % (len(samples_chunk), self.window*self.window*2+1, 1))
            for data, r in samples_chunk:
                f.write("%s\n%f\n"  % (' '.join('%f' % (d,) for d in data), r))

        self.max_iterations = min(self.max_iterations, 512)
        while self.max_iterations < 4096:
            iterations_between_reports = (self.max_iterations / 10) or 1

            t0 = time.time()
            self.net.train_on_file(self.dataset_filename,
                                   self.max_iterations,
                                   iterations_between_reports,
                                   desired_error)
            td = time.time() - t0

            print "[.] %s in %.3fsec sq_error_all=%.16f sq_error_set=%.16f" % (
                len(samples_chunk), td, self.sq_error()*1000., self.sq_error(samples_chunk))
            self.save()

            if td < 15.:
                self.max_iterations *= 2
            elif td > 30:
                self.max_iterations /= 2

    def save(self):
        tmpfile = self.filename + '~net~'
        self.net.save(tmpfile)
        with open(tmpfile, 'rb') as f:
            network_data = f.read()
        os.unlink(tmpfile)
        with open(self.filename + '~', 'wb') as f:
            out = pickle.Pickler(f)
            out.dump( (const.PWINDOW, self.window) )
            out.dump( (const.PSIZE, self.size) )
            out.dump( (const.PRATIO, self.ratio) )
            out.dump( (const.PMULTIPLIER, self.multiplier) )
            out.dump( (const.PNETWORK, network_data) )
            out.dump( (const.PTYPE, self.type) )
            f.flush()
        os.rename(self.filename + '~', self.filename)

    def load(self):
        with open(self.filename, 'rb') as f:
            inp = pickle.Unpickler(f)
            while True:
                try:
                    k, v = inp.load()
                except EOFError:
                    break
                if k == const.PNETWORK:
                    network_data = v
                elif k == const.PWINDOW:
                    if self.window:
                        if self.window != v:
                            print "[!] window differs"
                    else:
                        self.window = v
                elif k == const.PSIZE:
                    if self.size:
                        if self.size != v:
                            print "[!] size differs"
                    else:
                        self.size = v
                elif k == const.PRATIO:
                    if self.ratio:
                        if self.ratio != v:
                            print "[!] ratio differs"
                    else:
                        self.ratio = v
                elif k == const.PMULTIPLIER:
                    if self.multiplier:
                        if self.multiplier != v:
                            print "[!] multiplier differs"
                    else:
                        self.multiplier = v
                elif k == const.PTYPE:
                    if self.type:
                        if self.type != v:
                            print "[!] type differs"
                    else:
                        self.type = v
                else:
                    x.FATAL("%r" % (k,))

        self.net = libfann.neural_net()
        tmpfile = self.filename + '~net~'
        with open(tmpfile, 'wb') as f:
            f.write(network_data)
        self.net.create_from_file(tmpfile)
        os.unlink(tmpfile)
        self._set_funs()


    def run(self, data):
        return self.net.run(data)[0]

    def sq_error(self, samples=None):
        if samples is None:
            samples = self.samples
        sq_error = sum( (r - self.run(data)) ** 2
                        for data, r in samples )
        return math.sqrt(sq_error / len(samples))


    def build_datasets(self, chunks):
        list_of_c = array.array('I', xrange(len(self.samples)))
        random.shuffle(list_of_c)
        while list_of_c:
            yield [self.samples[list_of_c.pop()]
                   for _ in xrange(min(chunks, len(list_of_c)))]
