#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import matplotlib.transforms as mtransforms
import matplotlib.projections as mproj

class DataAxes(Axes):
    name = 'data'
    def format_coord(self, x, y):
        normal_part = Axes.format_coord(self, x, y)
        if self.images:
            # Most recent image is usually on top
            im = self.images[-1]
            j, i = self._coords2index(im, x, y)
            z = im.get_array()[j, i]
            return "Value: %f, %s" % (z, normal_part)
        return normal_part

    @staticmethod
    def _coords2index(im, x, y):
        """
        Convert data coordinates to index coordinates of the image array.
        Credit: mpldatacursor developers. Copyright (c) 2012. BSD License
        Modified from original found at:
        https://github.com/joferkington/mpldatacursor/blob/master/mpldatacursor/pick_info.py
        """
        xmin, xmax, ymin, ymax = im.get_extent()
        if im.origin == 'upper':
            ymin, ymax = ymax, ymin
        im_shape = im.get_array().shape[:2]
        data_extent = mtransforms.Bbox([[ymin, xmin], [ymax, xmax]])
        array_extent = mtransforms.Bbox([[0, 0], im_shape])
        trans = (mtransforms.BboxTransformFrom(data_extent) +
                 mtransforms.BboxTransformTo(array_extent))
        j, i = trans.transform_point([y, x]).astype(int)
        # Clip the coordinates to the array bounds.
        return min(max(j, 0), im_shape[0] - 1), min(max(i, 0), im_shape[1] - 1)

# Register DataAxes so that it can be used like any other Axes
# Registered using the 'name' attribute, so it will be accessible as 'data'.
mproj.projection_registry.register(DataAxes)

if __name__ == '__main__':
    ys, xs = np.mgrid[0:5:0.1, 0:4:0.1]
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection='data')
    ax.imshow(xs, extent=(xs[0, 0], xs[0, -1], ys[0, 0], ys[-1, 0]),
              origin='lower', cmap='gray')
    plt.show()
