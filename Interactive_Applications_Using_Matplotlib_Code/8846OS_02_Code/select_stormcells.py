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
    pc = PolyCollection(polygons[frame], lw=[1]*len(polygons[frame]),
                        facecolors='k', zorder=1, edgecolors='w', alpha=0.45,
                        visible=(not frame), picker=True)
    ax.add_collection(pc)
    polycolls.append(pc)

ax.autoscale(True)

class PickControl:
    def __init__(self, fig):
        self.fig = fig
        self._pickers = []
        self._pickcids = []

    def connect_picks(self):
        for i, picker in enumerate(self._pickers):
            if self._pickcids[i] is None:
                cid = self.fig.canvas.mpl_connect('pick_event', picker)
                self._pickers[i] = cid

    def disconnect_picks(self):
        for i, cid in enumerate(self._pickcids):
            if cid is not None:
                self.fig.canvas.mpl_disconnect(cid)
                self._pickcids[i] = None

    def add_pick_action(self, picker):
        if not callable(picker):
            raise ValueError("Invalid picker. Picker function is not callable")
        if  picker in self._pickers:
            raise ValueError("Picker is already in the list of pickers")
        self._pickers.append(picker)
        cid = self.fig.canvas.mpl_connect('pick_event', picker)
        self._pickcids.append(cid)

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

class ControlSys(KeymapControl, PickControl):
    def __init__(self, fig, im, data, polygons):
        self.fig = fig
        self.im = im
        self.data = data
        self.i = 0
        self.selected = None
        self.polygons = polygons
        self._hidekey = None
        self._hidecid = None
        KeymapControl.__init__(self, fig)
        PickControl.__init__(self, fig)

        self.add_key_action('left', 'Back a frame',
                            lambda : self.change_frame(-1))
        self.add_key_action('right', 'Forward a frame',
                            lambda : self.change_frame(1))
        self.add_key_action('H', 'Hide polygons while holding this key',
                            self.enable_hide)
        self.add_key_action('h', 'Display this help menu',
                            self.display_help_menu)
        self.add_pick_action(self.select_stormcell)

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

    def select_stormcell(self, event):
        if event.artist not in self.polygons:
            return
        ind = event.ind[0]
        lws = event.artist.get_linewidths()
        if (self.i, ind) != self.selected:
            if self.selected is not None:
                prev_i, prev_ind = self.selected
                prev_lws = self.polygons[prev_i].get_linewidths()
                prev_lws[prev_ind] = 1
                self.polygons[prev_i].set_linewidths(prev_lws)

            lws[ind] = 4
            self.selected = (self.i, ind)
        else:
            lws[ind] = 1
            self.selected = None

        event.artist.set_linewidths(lws)
        self.fig.canvas.draw_idle()


ctrl_sys = ControlSys(fig, im, data, polycolls)
plt.show()
