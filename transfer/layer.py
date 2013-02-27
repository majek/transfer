import itertools
import array
import PIL.Image

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
        img = PIL.Image.new('L', self.size)
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

    def delta(self, l):
        n = Layer(self.size)
        for c in xrange(self.size[0] * self.size[1]):
            n.a[c] = abs(l.a[c] - self.a[c])
        return n

def save(layers, filename):
    out = PIL.Image.merge("RGB", (layers[0].to_image(),
                                  layers[1].to_image(),
                                  layers[2].to_image()))
    out.save(filename)
