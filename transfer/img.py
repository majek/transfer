from __future__ import print_function
from PIL import Image, ImageDraw
import math
import array
import itertools


def _grow((rows, cols), d, r, c):
    d[r, c] = (0,0,0)
    opts = []
    if r+1 < rows:
        opts.append( (r+1, c) )
    if c+1 < cols:
        opts.append( (r, c+1) )
    rets = [(r,c)]
    for (a,b) in opts:
        if d[a,b] == (127, 127, 127):
            rets += _grow((rows, cols), d, a, b)
    return rets

MARKER_COLOR = (127, 127, 127)

class Result(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.size = ((p2[0] - p1[0]) or 1,
                     (p2[1] - p1[1]) or 1)
        self.centre = (average(p1[0], p2[0]),
                       average(p1[1], p2[1]))

def decipher_result_file(filename):
    results = []
    om = Image.open(filename)
    d = om.load()
    for r in xrange(om.size[0]):
        for c in xrange(om.size[1]):
            if d[r, c] == MARKER_COLOR:
                rets = _grow(om.size, d, r, c)
                rows, cols = zip(*rets)
                # clear all the pixels within detected rectangle
                for aa in xrange(min(rows), max(rows)):
                    for bb in xrange(min(cols), max(cols)):
                        d[aa, bb]  = (0,0,0)
                results.append(Result((min(rows), min(cols)),
                                      (max(rows), max(cols))))
    return results



def average(*a):
    return sum(a) / len(a)


class Layer(object):
    def __init__(self, size, data=None):
        self.size = size
        if data is not None:
            self.a = array.array('f', data)
            assert len(self.a) == size[0] * size[1]
        else:
            self.a = array.array('f', itertools.repeat(0., size[0] * size[1]))

    def __getitem__(self, k):
        # assert 0 <= k[0] < self.size[0]
        # assert 0 <= k[1] < self.size[1]
        return self.a[k[0] + self.size[0] * k[1]]

    def __setitem__(self, k, v):
        # assert 0 <= k[0] < self.size[0]
        # assert 0 <= k[1] < self.size[1]
        self.a[k[0] + self.size[0] * k[1]] = v

    def normalize(self):
        mi = min(self.a); ma = max(self.a)
        delta = float(ma - mi)
        self.a = array.array('f', ((v - mi) / delta for v in self.a))


    def bigger(self, extend):
        (r, c) = extend
        a = array.array('f')
        for _ in xrange(c):
            a.extend(itertools.repeat(0., r+r+self.size[0]))
        for y in xrange(self.size[1]):
            a.extend(itertools.chain(
                    itertools.repeat(0., r),
                    self.a[self.size[0] * y: self.size[0] * (y+1)],
                    itertools.repeat(0., r),
                    ) )
        for _ in xrange(c):
            a.extend(itertools.repeat(0., r+r+self.size[0]))
        # print(len(a),self.size, extend, self.size[0]+2*r, self.size[1]+2*c,
        #       (self.size[0]+2*r)* (self.size[1]+2*c))
        return Layer((self.size[0]+2*r, self.size[1]+2*c), a)

    def to_image(self):
        img = Image.new('L', self.size)
        img.putdata(array.array('B', (int(v*255.) for v in self.a)))
        return img

    def windows_fun(self, size):
        size = (size/2)*2
        big = self.bigger((size/2, size/2))
        bsz = big.size[0]
        def gen(c):
            y = c / bsz
            x = c % bsz
            return Layer((size, size),
                         itertools.chain(*[big.a[x + bsz*yy : x + size + bsz*yy]
                                           for yy in xrange(y, y+size)]))
        return gen


    def windows(self, size):
        size = (size/2)*2
        big = self.bigger((size/2, size/2))
        bsz = big.size[0]
        for x in xrange(big.size[0]-size):
            for y in xrange(big.size[1]-size):
                yield lambda: Layer((size, size),
                    itertools.chain(*[big.a[x + bsz*yy : x + size + bsz*yy]
                                         for yy in xrange(y, y+size)]))

def load_source(filename):
    # assuming two layer 16-bit tiff
    im = Image.open(filename)

    for layer in range(2):
        im.seek(layer)
        assert im.mode == 'I;16'

    layers = []
    for layer in range(2):
        im.seek(layer)
        layer = Layer(im.size, im.getdata())
        layer.normalize()
        layers.append( layer )
    return layers


def _prepare_to_save(layers):
    ilrs = [layers[0].to_image(),
            layers[1].to_image(),
            Image.new('L', layers[0].size)]
    return ilrs

def save_rectangle(layers, results, filename):
    ilrs = _prepare_to_save(layers)
    redl = ilrs[2]
    for r in results:
        ImageDraw.Draw(redl).rectangle([r.p1, r.p2], outline=255)

    out = Image.merge("RGB", (ilrs[2], ilrs[0], ilrs[1]))
    out.save(filename)

def save_results_layer(layers, results_layer, filename):
    ilrs = _prepare_to_save(layers)
    ilrs[2] = results_layer.to_image()
    out = Image.merge("RGB", (ilrs[2], ilrs[0], ilrs[1]))
    out.save(filename)


def _draw_thing(layer, (x, y), (width_x, width_y), (size_x, size_y), multiplier):
    aspect = float(width_x) / width_y
    dist = lambda a, b: math.sqrt(((a - x) / aspect)**2 +
                                  ((b - y))**2)

    for a in xrange(max(0, x - width_x * 2), min(x + width_x * 2, size_x-1)):
        for b in xrange(max(0, y - width_y * 2), min(y + width_y * 2, size_y-1)):
            d = dist(a, b) / max(width_x*multiplier, width_y*multiplier)
            intensity = (1. - d) ** 2 if (1 - d) > 0 else 0
            layer[a, b] = max(layer[a, b], min(1.0, intensity))


def results_to_layer(size, results, multiplier=1.0):
    l = Layer(size)
    for result in results:
        _draw_thing(l, result.centre, result.size, size, multiplier)
        l[result.centre[0], result.centre[1]] = 1.
    return l




'''
                #if False:
                #     ImageDraw.Draw(lrs[2]).rectangle([(min(rows), min(cols)),
                #                                       (max(rows), max(cols))],
                #                                      outline=255)
                #
                # draw_thing(redl,
                #            (average(max(rows), min(rows)),
                #             average(max(cols), min(cols))),
                #            ((max(rows)-min(rows)) or 1,
                #             (max(cols)-min(cols)) or 1),
                #            om.size, multiplier=1.5)
def read_data(input):
    im = Image.open(input.input_filename)

    lrs = [Image.new('L', im.size), Image.new('L', im.size), Image.new('L',im.size)]
    for layer in range(2):
        im.seek(layer)
        lrs[layer].putdata(map(lambda v: int(v*256.),
                               normalize(im.getdata())))

    redl = lrs[2].load()

    if input.output_filename:
        om = Image.open(input.output_filename)
        d = om.load()
        for r in xrange(om.size[0]):
            for c in xrange(om.size[1]):
                if d[r, c] == MARKER_COLOR:
                    rets = grow(om.size, d, r, c)
                    rows, cols = zip(*rets)
                    # clear all the pixels within detected rectangle
                    for aa in xrange(min(rows), max(rows)):
                        for bb in xrange(min(cols), max(cols)):
                            d[aa, bb]  = (0,0,0)
                    if False:
                        ImageDraw.Draw(lrs[2]).rectangle([(min(rows), min(cols)),
                                                          (max(rows), max(cols))],
                                                         outline=255)
                    draw_thing(redl,
                               (average(max(rows), min(rows)),
                                average(max(cols), min(cols))),
                               ((max(rows)-min(rows)) or 1,
                                (max(cols)-min(cols)) or 1),
                               om.size, multiplier=1.5)

    out = Image.merge("RGB", (lrs[2],
                              lrs[0],
                              lrs[1]))
    out.save(input.attempt_filename())
'''
