import PIL.Image

from . import extra as x
from . import EXIF
from . import layer


def load_source(fullname, desired_size):
    img = PIL.Image.open(fullname)

    assert img.size == desired_size

    for layer_no in range(2):
        img.seek(layer_no)
        assert img.mode == 'I;16'

    try:
        img.seek(3)
    except EOFError:
        ok = True
    if not ok: x.FATAL("%r must have exactly two layers" % (fullname,))

    with open(fullname, 'rb') as f:
        exif_data = EXIF.process_file(f)

    order = []
    for k, v in exif_data.iteritems():
        if 'PageName' in k:
            if 'C=Dapi' in v.values:
                order.append('DAPI')
            elif 'C=GFP' in v.values:
                order.append('GFP')
            else:
                x.FATAL("%r EXIF doesn't show GFP/DAPI setting %r" % (fullname, v))
    if len(set(order)) != 2 or len(order) != 2:
        x.FATAL("%r EXIF doesn't show correct GFP/DAPI settings" % (fullname,))

    layers = {}
    for layer_no in range(2):
        img.seek(layer_no)
        l = layer.Layer(img.size, img.getdata())
        l.normalize()
        layers[order.pop(0)] = l
    return layers

