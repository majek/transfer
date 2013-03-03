import argparse
import sys
import cPickle as pickle
import itertools
import random
import array
import os.path

from . import fnet
from . import extra as x
from . import layer
from . import loader
from . import result


def main(argv):
    parser = argparse.ArgumentParser(description='Draw results of a net')
    parser.add_argument('directory', nargs='+',
                        help='directories to traverse')
    parser.add_argument('--network',
                        help='loaded network')
    opts = parser.parse_args(argv)

    if not opts.network:
        opts.network = 'network.fann'

    net = fnet.Network()
    net.load(opts.network)
    size = net.size
    max_c = size[0] * size[1]
    window = net.window

    for name, prefix in itertools.chain(*[x.read_directory(dirname)
                                          for dirname in opts.directory]):
        print "[.] Loading %r" % (prefix + '-source.tif',)
        layers = loader.load_source(prefix + '-source.tif', size)
        layers['R'] = layer.Layer(size)

        if os.path.exists(prefix + '-output.tif'):
            results = result.load_results(prefix + '-output.tif', size)
            layers['O'] = result.results_to_layer(size, results, multiplier=net.multiplier)

        def save(fract):
            print "[ ] %.1f%%" % (fract*100.,)
            if False:
                layer.save([layers['R'],
                            layers['GFP'],
                            layers['DAPI']],
                           prefix + '-network.png')
            layer.save([layers['R'],
                        layers['R'],
                        layers['R']],
                       prefix + '-raw-network.png')
            if 'O' in layers:
                layers['D'] = layers['O'].delta(layers['R'])
                layer.save([layers['D'],
                            layers['D'],
                            layers['D']],
                           prefix + '-error.png')


        list_of_c = array.array('I', xrange(max_c))
        random.shuffle(list_of_c)
        w1 = layers['GFP'].windows_fun(window)
        w2 = layers['DAPI'].windows_fun(window)
        i = 0; res = layers['R'].a
        for c in list_of_c:
            r = net.run(
                array.array('f', itertools.chain([1.], w1(c).a, w2(c).a))
                )
            res[c] = min(max(0,r),1)
            i += 1
            if i % 10000 == 0: save(float(i) / max_c)
        save(1.0)


if __name__ == "__main__":
    main(sys.argv[1:])
