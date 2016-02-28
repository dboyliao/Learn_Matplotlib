from __future__ import print_function
from collections import OrderedDict
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

class KeymapControl:
    def __init__(self, fig):
        self.fig = fig
        # Deactivate the default keymap
        fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)
        self._keymap = OrderedDict()
        # Activate my keymap
        self.connect_keymap()
        self._lastkey = None

    def connect_keymap(self):
        self._keycid = self.fig.canvas.mpl_connect('key_press_event',
                                                   self.keypress)

    def disconnect_keymap(self):
        if self._keycid is not None:
            self.fig.canvas.mpl_disconnect(self._keycid)
            self._keycid = None

    def add_key_action(self, key, description, action_func):
        if not callable(action_func):
            raise ValueError("Invalid key action. Key '%s' Description '%s'"
                             " - action function is not a callable" %
                             (key, description))
        if key in self._keymap:
            raise ValueError("Key '%s' is already in the keymap" % key)
        self._keymap[key] = (description, action_func)

    def keypress(self, event):
        action_tuple = self._keymap.get(event.key, None)
        if action_tuple:
            self._lastkey = event.key
            action_tuple[1]()

    def display_help_menu(self):
        print("Help Menu")
        print("Key         Action")
        print("=========== ============================================")
        for key, (description, _) in self._keymap.items():
            print("%11s %s" % (key, description))

class ControlSys(KeymapControl):
    def __init__(self, fig, im, data, polycolls):
        self.fig = fig
        self.im = im
        self.data = data
        self.polygons = polycolls
        self.i = 0
        self._hidekey = None
        self._hidecid = None
        KeymapControl.__init__(self, fig)

        self.add_key_action('left', 'Back a frame',
                            lambda : self.change_frame(-1))
        self.add_key_action('right', 'Forward a frame',
                            lambda : self.change_frame(1))
        self.add_key_action('H', 'Hide polygons while holding this key',
                            self.enable_hide)
        self.add_key_action('h', 'Display this help menu',
                            self.display_help_menu)

    def change_frame(self, frame_delta):
        newi = self.i + frame_delta
        if newi >= self.data.shape[0]:
            newi = self.data.shape[0] - 1
        if newi < 0:
            newi = 0
        if newi != self.i:
            self.polygons[self.i].set_visible(False)
            self.polygons[newi].set_visible(True)
            self.im.set_data(self.data[newi])
            self.fig.canvas.draw_idle()
            self.i = newi

    def enable_hide(self):
        self.disconnect_keymap()
        self._hidekey = self._lastkey.lower()
        self._hidecid = self.fig.canvas.mpl_connect('key_release_event',
                                                    self.release_hide)
        self.polygons[self.i].set_visible(False)
        self.fig.canvas.draw_idle()

    def release_hide(self, event):
        if event.key.lower() == self._hidekey and self._hidecid is not None:
            self.fig.canvas.mpl_disconnect(self._hidecid)
            self._hidekey = None
            self._hidecid = None
            self.connect_keymap()
            self.polygons[self.i].set_visible(True)
            self.fig.canvas.draw_idle()

ctrl_sys = ControlSys(fig, im, data, polycolls)
plt.show()
