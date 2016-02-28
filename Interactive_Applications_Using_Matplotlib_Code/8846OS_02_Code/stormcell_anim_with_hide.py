import matplotlib.pyplot as plt
from scipy.io import netcdf_file
from matplotlib.collections import PolyCollection
from tutorial import polygon_loader

ncf = netcdf_file('KTLX_20100510_22Z.nc')
data = ncf.variables['Reflectivity']
lats = ncf.variables['lat']
lons = ncf.variables['lon']
i = 0

fig, ax = plt.subplots(1, 1)
im = ax.imshow(data[i], origin='lower',
               extent=(lons[0], lons[-1], lats[0], lats[-1]),
               vmin=0, vmax=80, cmap='gist_ncar')
fig.colorbar(im)

polygons = polygon_loader('polygons.shp')
polycolls = []
for frame in sorted(polygons):
    pc = PolyCollection(polygons[frame], linewidths=3, facecolors='k', zorder=1,
                    edgecolors='w', alpha=0.45, visible=(not frame))
    ax.add_collection(pc)
    polycolls.append(pc)
ax.autoscale(True)

class ControlSys:
    def __init__(self, fig, im, data, polycolls):
        self.fig = fig
        self.im = im
        self.data = data
        self.polygons = polycolls
        self.i = 0
        # Deactivate the default keymap
        fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)
        # Activate my keymap
        self._keycid = self.fig.canvas.mpl_connect('key_press_event',
                                                   self.keypress)
        self._hidecid = None

    def keypress(self, event):
        previ = self.i
        if event.key == 'left' and self.i > 0:
            self.i -= 1
        elif event.key == 'right' and self.i < (self.data.shape[0] - 1):
            self.i += 1
        elif event.key == 'H':
            if self._keycid is not None:
                self.fig.canvas.mpl_disconnect(self._keycid)
                self._keycid = None
            self._hidecid = self.fig.canvas.mpl_connect('key_release_event',
                                                        self.release_hide)
            self.polygons[self.i].set_visible(False)
            self.fig.canvas.draw_idle()
        if previ != self.i:
            self.polygons[previ].set_visible(False)
            self.polygons[self.i].set_visible(True)
            self.im.set_data(self.data[self.i])
            self.fig.canvas.draw_idle()

    def release_hide(self, event):
        if event.key == 'H' and self._hidecid is not None:
            self.fig.canvas.mpl_disconnect(self._hidecid)
            self._hidecid = None
            self._keycid = self.fig.canvas.mpl_connect('key_press_event',
                                                   self.keypress)
            self.polygons[self.i].set_visible(True)
            self.fig.canvas.draw_idle()

ctrl_sys = ControlSys(fig, im, data, polycolls)
plt.show()
