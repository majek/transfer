import argparse
import sys
import itertools
import os.path
import cPickle as pickle
import array
import random

from . import extra as x
from . import loader
from . import result
from . import img
from . import layer
from . import const

SIZE = (672, 512)


def main(argv):
    parser = argparse.ArgumentParser(description='Generate training data from a set of tiffs.')
    parser.add_argument('directory', nargs='+',
                        help='directories to traverse')
    parser.add_argument('--window', type=int, default=8,
                        help='window size (default: 8)')
    parser.add_argument('--output', type=argparse.FileType('wb', 0),
                        help='output file')
    parser.add_argument('--multiplier', type=float, default=1.2,
                        help='multiplier')
    parser.add_argument('--ratio', type=float, default=1.0,
                        help='ratio')
    parser.add_argument('--type', default="ovalshade",
                        help='type of output data [rect, oval, ovalshade]')
    parser.add_argument('--save', default=False, type=bool,
                        help='save intermediate images form')
    opts = parser.parse_args(argv)

    assert opts.type in ['rect', 'oval', 'ovalshade']

    size = SIZE
    max_c = size[0] * size[1]
    suffix_window = '%s_%s_%.1f' % (opts.window, opts.type, opts.multiplier)
    suffix_nowindow = '%s_%.1f' % (opts.type, opts.multiplier)

    if not opts.output:
        opts.output = open('dataset_%s.pickle' % (suffix_window,), 'wb')


    files = []
    for name, prefix in itertools.chain(*[x.read_directory(dirname)
                                          for dirname in opts.directory]):
        if os.path.exists(prefix + '-output.tif'):
            files.append( (name, prefix) )

    print "[+] savnig to %r" % (opts.output.name,)
    out = pickle.Pickler(opts.output, protocol=-1)
    out.dump( (const.PSIZE, size) )
    out.dump( (const.PWINDOW, opts.window) )
    out.dump( (const.PRATIO, opts.ratio) )
    out.dump( (const.PMULTIPLIER, opts.multiplier) )

    for (name, prefix) in files:
        print "[.] Loading %r" % (prefix + '-source.tif',)
        layers = loader.load_source(prefix + '-source.tif', size)
        results = result.load_results(prefix + '-output.tif', size)
        layers['T'] = result.results_to_rectangle_layer(size, results)
        layers['R'] = result.results_to_layer(size, results, opts.multiplier, opts.type)
        if False:
            layer.save([layer.Layer(size),
                        layers['GFP'],
                        layers['DAPI']],
                       prefix + '-source.png')
            layer.save([layers['T'],
                        layers['GFP'],
                        layers['DAPI']],
                       prefix + '-rect.png')
            layer.save([layers['R'],
                        layers['GFP'],
                        layers['DAPI']],
                       prefix + '-res.png')

        if opts.save:
            layer.save([layers['R'],
                        layers['GFP'],
                        layers['DAPI']],
                       prefix + '-expected-' + suffix_nowindow + '.png')

        w1 = layers['GFP'].windows_fun(opts.window)
        w2 = layers['DAPI'].windows_fun(opts.window)
        r  = layers['R'].a

        positive = 0
        samples = []

        for c in xrange(max_c):
            if r[c] != 0.0:
                s = [list(itertools.chain((1.0,), w1(c).a, w2(c).a)), r[c]]
                samples.append( s )
                positive += 1
        print "[ ] %s positive samples" % (positive, )

        negative = 0
        list_of_c = array.array('I', xrange(max_c))
        random.shuffle(list_of_c)
        while negative  < positive * opts.ratio and list_of_c:
            c = list_of_c.pop()
            if r[c] == 0.0:
                s = [list(itertools.chain((1.0,), w1(c).a, w2(c).a)), r[c]]
                samples.append( s )
                negative += 1
        print "[ ] %s negative samples" % (negative, )

        out.dump( (const.PSAMPLES, samples) )
        opts.output.flush()
    opts.output.close()

if __name__ == "__main__":
    main(sys.argv[1:])
