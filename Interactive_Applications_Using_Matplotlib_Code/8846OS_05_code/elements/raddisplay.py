import numpy as np
import matplotlib.pyplot as plt

class RadarDisplay(object):
    def __init__(self, ax, lats, lons):
        self.im = None
        cmap = plt.get_cmap('gist_ncar')
        cmap.set_under('lightgrey')
        self.initialize_display(ax, lats, lons)

    def initialize_display(self, ax, lats, lons):
        if self.im is not None:
            self.im.remove()
        fake_data = np.zeros((lats.shape[0], lons.shape[0]))
        self.im = ax.imshow(fake_data, origin='lower',
                            extent=(lons[0], lons[-1], lats[0], lats[-1]),
                            vmin=0.1, vmax=80, cmap='gist_ncar')

    def update_display(self, data):
        self.im.set_data(data)

