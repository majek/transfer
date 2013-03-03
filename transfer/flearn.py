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
    parser.add_argument('--error', type=float, default=0.0001,
                        help='desired training error (default: 0.0001)')
    parser.add_argument('--chunk', type=int, default=128,
                        help='starting chunk size (default: 128)')
    opts = parser.parse_args(argv)

    force_new = True
    if opts.network and os.path.exists(opts.network):
        force_new = False

    if not opts.network:
        opts.network = 'network.fann'

    net = fnet.Network(opts.network)

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
            elif v[0] == const.PTYPE:
                etype = v[1]
            elif v[0] == const.PSAMPLES:
                for data, r in v[1]:
                    net.addSample(array.array('f', data), r)
            else:
                x.FATAL('unknown key %r' % (v[0],))
    net.preset(window, ratio, size, multiplier, etype)
    if force_new:
        print "[+] New network file %r" % (opts.network,)
        net.new()
    else:
        print "[+] Loading net from %r" % (opts.network,)
        net.load()

    print "[.] Loaded %i samples" % (len(net.samples),)

    print "[.] sq_errorr=%.16f" % (net.sq_error() * 1000.,)

    try:
        chunks =  min(opts.chunk, (len(net.samples) / 2)+1)
        while chunks < len(net.samples):
            chunks = min(chunks * 2, len(net.samples))
            print "[*] Training set size %i" % (chunks,)
            for chunk in net.build_datasets(chunks):
                print "[*] *** New chunk"
                net.train(chunk, opts.error)
    except KeyboardInterrupt:
        pass
    finally:
        os.unlink(net.dataset_filename)

    net.save()
    print "[.] sq_errorr=%.16f" % (net.sq_error()*1000.,)
    print "[!] exit"
