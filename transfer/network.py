from pybrain.tools.shortcuts import buildNetwork
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.structure import FeedForwardNetwork, FullConnection, SigmoidLayer
from pybrain.tools.customxml import NetworkWriter, NetworkReader

import array
import time
import pickle
import itertools
import random
import os

from . import const

def _new_2h_net(window):
    net     = FeedForwardNetwork()
    inl     = SigmoidLayer(window*window*2+1)
    hidden1 = SigmoidLayer(window*window*2)
    hidden2 = SigmoidLayer(window)
    outl    = SigmoidLayer(1)
    net.addInputModule(inl)
    net.addModule(hidden1)
    net.addModule(hidden2)
    net.addOutputModule(outl)
    c1 = FullConnection(inl, hidden1)
    c2 = FullConnection(hidden1, hidden2)
    c3 = FullConnection(hidden2, outl)
    net.addConnection(c1)
    net.addConnection(c2)
    net.addConnection(c3)
    return net

def _new_1h_net(window):
    net     = FeedForwardNetwork()
    inl     = SigmoidLayer(window*window*2+1)
    hidden1 = SigmoidLayer(window*window*2)
    outl    = SigmoidLayer(1)
    net.addInputModule(inl)
    net.addModule(hidden1)
    net.addOutputModule(outl)
    c1 = FullConnection(inl, hidden1)
    c2 = FullConnection(hidden1, outl)
    net.addConnection(c1)
    net.addConnection(c2)
    return net


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

    def new(self, type):
        if type == "auto":
            self.net = buildNetwork(self.window*self.window*2+1, self.window*self.window*2, 1)
        elif type == "1h":
            self.net = _new_1h_net(self.window)
        elif type == "2h":
            self.net = _new_2h_net(self.window)
        else:
            x.FATAL("")
        self.net.sortModules()

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

        tmpfile = filename + '~net~'
        with open(tmpfile, 'wb') as f:
            f.write(network_data)
        self.net = NetworkReader.readFrom(tmpfile)
        os.unlink(tmpfile)
        self.net.sortModules()

    def save(self, filename):
        tmpfile = filename + '~net~'
        NetworkWriter.writeToFile(self.net, tmpfile)
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

    def addSample(self, data, result):
        self.samples.append( (data, result) )

    def batchedDatasets(self, chunk):
        list_of_c = array.array('I', xrange(len(self.samples)))
        random.shuffle(list_of_c)
        while list_of_c:
            ds = SupervisedDataSet(self.window*self.window*2+1, 1)
            for i in xrange(min(chunk, len(list_of_c))):
                data, r = self.samples[list_of_c.pop()]
                ds.addSample(data, (r,))
            yield ds

    def batchedTrainers(self, chunk):
        for ds in self.batchedDatasets(chunk):
            yield BackpropTrainer(self.net, ds)


    # def train(self):
    #     t0 = time.time()

    #     # with open('f.pickle', 'w') as f:
    #     #     f.write(pickle.dumps([(data, result[0]) for data,result in self.ds]))

    #     trainer = BackpropTrainer(self.net, self.ds)
    #     #print("[ ] untilconvergence....")
    #     try:
    #         pass
    #         #trainer.trainUntilConvergence()
    #     except KeyboardInterrupt:
    #         pass
    #     print("[ ] normaltraining....")
    #     try:
    #         for i in range(20):
    #             t = trainer.train()
    #             print("[ ] trained %f %f" % (t, self.sq_error()))
    #     except KeyboardInterrupt:
    #         pass
    #     t1 = time.time()
    #     return t1-t0

    def run(self, data):
        return self.net.activate(data)[0]

    def sq_error(self):
        return sum( (r - self.run(data)) ** 2
                    for data, r in self.samples )
