from pyfann import libfann
import os
import time
import signal
import math
import cPickle as pickle

from . import const


class Network(object):
    window = None
    size = None
    ratio = None
    multiplier = None

    def __init__(self):
        self.samples = []

    def preset(self, window, ratio, size, multiplier):
        self.window = window
        self.ratio = ratio
        self.size = size
        self.multiplier = multiplier

    def addSample(self, data, result):
        self.samples.append( (data, result) )

    def new(self):
        self.net = libfann.neural_net()
        connection_rate = 1
        learning_rate = 0.7
        num_input = self.window*self.window*2+1
        num_hidden = self.window*self.window*2
        num_output = 1

        self.net.create_sparse_array(connection_rate,
                                     (num_input, num_hidden, num_output))
        self.net.set_learning_rate(learning_rate)
        self.net.set_activation_function_output(libfann.SIGMOID_SYMMETRIC_STEPWISE)

    def train(self, network_filename):
        tmpfile = 'fann.data'
        print "[.] preparing data for fann"
        with open(tmpfile, 'wb') as f:
            f.write("%i %i %i\n" % (len(self.samples), self.window*self.window*2+1, 1))
            for data, r in self.samples:
                f.write("%s\n%f\n"  % (' '.join('%f' % (d,) for d in data), r))

        print "[ ] learning"
        desired_error = 0.0001
        max_iterations = 20
        iterations_between_reports = 0
        td = 1.
        while td >= 1.:
            t0 = time.time()
            try:
                self.net.train_on_file(tmpfile,
                                       max_iterations,
                                       iterations_between_reports,
                                       desired_error)
            except KeyboardInterrupt:
                break
            td = time.time() - t0
            sqe = self.sq_error()
            print "[.] done in %.3fsec sq_errorr=%.16f" % (td, sqe*1000.)
            self.save(network_filename)

        self.save(network_filename)
        os.unlink(tmpfile)

    def save(self, filename):
        tmpfile = filename + '~net~'
        self.net.save(tmpfile)
        with open(tmpfile, 'rb') as f:
            network_data = f.read()
        os.unlink(tmpfile)
        with open(filename + '~', 'wb') as f:
            out = pickle.Pickler(f)
            out.dump( (const.PWINDOW, self.window) )
            out.dump( (const.PSIZE, self.size) )
            out.dump( (const.PRATIO, self.ratio) )
            out.dump( (const.PMULTIPLIER, self.multiplier) )
            out.dump( (const.PNETWORK, network_data) )
            f.flush()
        os.rename(filename + '~', filename)

    def load(self, filename):
        with open(filename, 'rb') as f:
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
                else:
                    FATAL("%r" % (k,))

        self.net = libfann.neural_net()
        tmpfile = filename + '~net~'
        with open(tmpfile, 'wb') as f:
            f.write(network_data)
        self.net.create_from_file(tmpfile)
        os.unlink(tmpfile)


    def run(self, data):
        return self.net.run(data)[0]

    def sq_error(self):
        sq_error = sum( (r - self.run(data)) ** 2
                        for data, r in self.samples )
        return math.sqrt(sq_error / len(self.samples))
