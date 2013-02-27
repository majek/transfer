import math
import PIL.Image

from . import layer


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


def average(*a):
    return sum(a) / len(a)

MARKER_COLOR = (127, 127, 127)

class Result(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.size = ((p2[0] - p1[0]) or 1,
                     (p2[1] - p1[1]) or 1)
        self.centre = (average(p1[0], p2[0]),
                       average(p1[1], p2[1]))

def load_results(fullname, desired_size):
    results = []
    om = PIL.Image.open(fullname)
    assert om.size == desired_size

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

def results_to_rectangle_layer(size, results):
    l = layer.Layer(size)
    for r in results:
        for x in xrange(r.p1[0], r.p2[0]):
            l[x, r.p1[1]] = 1.0
            l[x, r.p2[1]] = 1.0
        for y in xrange(r.p1[1], r.p2[1]+1):
            l[r.p1[0], y] = 1.0
            l[r.p2[0], y] = 1.0
    return l



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
    l = layer.Layer(size)
    for result in results:
        _draw_thing(l, result.centre, result.size, size, multiplier)
        l[result.centre[0], result.centre[1]] = 1.
    return l