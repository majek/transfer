import argparse
import sys
import cPickle as pickle
import array
import itertools
import os

from . import extra as x
from . import const
from . import fnet

def main(argv):
    parser = argparse.ArgumentParser(description='Train artificial neural network')
    parser.add_argument('input', nargs='+', type=argparse.FileType('rb', 0),
                        help='pickle input files', )
    parser.add_argument('--network',
                        help='loaded and saved network')
    opts = parser.parse_args(argv)

    network_filename = 'network.fann'
    if opts.network:
        network_filename = opts.network

    if opts.network and os.path.exists(opts.network):
        print "[+] Loading net from %r" % (opts.network,)
        loadingfile = opts.network
    else:
        print "[+] No file %r" % (network_filename,)
        loadingfile = None


    net = fnet.Network()

    print "[ ] Loading training data set"
    for inputfile in opts.input:
        while True:
            inp = pickle.Unpickler(inputfile)
            try:
                v = inp.load()
            except EOFError:
                break
            if v[0] == const.PWINDOW:
                window = v[1]
            elif v[0] == const.PSIZE:
                size = v[1]
            elif v[0] == const.PRATIO:
                ratio = v[1]
            elif v[0] == const.PMULTIPLIER:
                multiplier = v[1]
            elif v[0] == const.PSAMPLES:
                for data, r in v[1]:
                    net.addSample(array.array('f', data), r)
            else:
                x.FATAL('unknown key %r' % (v[0],))
    net.preset(window, ratio, size, multiplier)
    if not loadingfile:
        net.new()
    else:
        net.load(loadingfile)

    print "[.] Training on %i datasets" % (len(net.samples),)

    net.train(network_filename)
    print "[!] exit"
