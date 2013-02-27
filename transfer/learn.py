import argparse
import sys
import cPickle as pickle
import array
import itertools
import os

from . import network
from . import extra as x
from . import const


def main(argv):
    parser = argparse.ArgumentParser(description='Train artificial neural network')
    parser.add_argument('input', nargs='+', type=argparse.FileType('rb', 0),
                        help='pickle input files', )
    parser.add_argument('--network',
                        help='loaded and saved network')
    parser.add_argument('--type', default='2h',
                        help='type of network 1h 2h auto')
    opts = parser.parse_args(argv)

    network_file = 'network.pickle'
    if opts.network:
        network_file = opts.network

    if opts.network and os.path.exists(opts.network):
        print "[+] Loading net from %r" % (opts.network,)
        loadingfile = opts.network
    else:
        print "[+] No file %r" % (network_file,)
        loadingfile = None


    net = None
    window = None

    net = network.Network()

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
                x.FATAL('blah %r' % (v[0],))
    net.preset(window, ratio, size, multiplier)
    if not loadingfile:
        net.new(opts.type)
    else:
        net.load(loadingfile)

    print "[.] Training on %i datasets" % (len(net.samples),)
    try:
        for chunk in (2**c for c in itertools.count(6)):
            chunk = min(chunk, len(net.samples))
            for trainer in net.batchedTrainers(chunk):
                print "[-] New sub dataset of %i" % (chunk,)
                trainer.trainUntilConvergence(maxEpochs=100, verbose=True, continueEpochs=20)
                # for i in range(10):
                #     t = trainer.train()
                t = trainer.train()
                print("[ ] trained %.16f" % (t,))
                t = trainer.train()
                print("[ ] trained %.16f sq_error=%.16f" % (t, net.sq_error()))
                net.save(network_file)
    except KeyboardInterrupt:
        pass
    print "[+] saved"
    net.save(network_file)



if __name__ == "__main__":
    main(sys.argv[1:])
