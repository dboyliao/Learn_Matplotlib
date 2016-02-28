from __future__ import print_function
from collections import OrderedDict
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import netcdf_file
from matplotlib.collections import PolyCollection
from tutorial import storm_loader, storm_saver

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

stormcells = storm_loader('polygons.shp')
polycolls = []
stormmap = []
for frame in range(np.max(stormcells['frame_index']) + 1):
    indexes = np.where(stormcells['frame_index'] == frame)[0]
    polygons = stormcells[indexes]['poly']
    pc = PolyCollection(polygons, lw=[1]*len(polygons),
                        facecolors='k', zorder=1, edgecolors='w', alpha=0.45,
                        visible=(not frame), picker=True)
    ax.add_collection(pc)
    polycolls.append(pc)
    stormmap.append(indexes)

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
    def __init__(self, fig, im, data, polygons, stormdata, stormmap):
        self.fig = fig
        self.im = im
        self.data = data
        self.i = 0
        self.selected = None
        self.polygons = polygons
        self.stormdata = stormdata
        self.stormmap = stormmap
        self._hidekey = None
        self._hidecid = None
        KeymapControl.__init__(self, fig)
        PickControl.__init__(self, fig)

        self._connect('frame_change', self.update_radar_display)
        self._connect('frame_change', self.display_stormcells)
        self._connect('select', self.hilite_stormcell)
        self._connect('deselect', self.lolite_stormcell)
        self._connect('hide', self.toggle_stormcells)
        self._connect('delete', self.delete_polygon)
        self._connect('delete', self.delete_stormcell)
        self._connect('save', lambda x: self.save_stormdata('polygons_new.shp'))
        self._connect('help', lambda x: self.display_help_menu())

        self.add_key_action('left', 'Back a frame',
                            lambda : self.change_frame(-1))
        self.add_key_action('right', 'Forward a frame',
                            lambda : self.change_frame(1))
        self.add_key_action('H', 'Hide polygons while holding this key',
                            self.enable_hide)
        self.add_key_action('d', 'Delete the selected stormcell',
                            self.delete_selected)
        self.add_key_action('w', 'Save the storm data',
                            lambda : self._emit('save', None))
        self.add_key_action('h', 'Display this help menu',
                            lambda : self._emit('help', None))
        self.add_pick_action(self.select_stormcell)

    def _emit(self, event, eventdata):
        self.fig.canvas.callbacks.process(event, eventdata)

    def _connect(self, event, callback):
        self.fig.canvas.mpl_connect(event, callback)

    # --- Stormcell editing methods ---
    def delete_selected(self):
        if self.selected is None:
            return
        # We only want to delete when the selection is in the current frame
        if self.i != self.selected[0]:
            return

        self._emit('delete', self.selected)
        self.selected = None
        self.fig.canvas.draw_idle()

    def delete_polygon(self, inds):
        frame_i, cell_i = inds
        paths = self.polygons[frame_i].get_paths()
        paths.pop(cell_i)
        lws = self.polygons[frame_i].get_linewidths()
        lws.pop(cell_i)

    def delete_stormcell(self, inds):
        frame_i, cell_i = inds
        # Take it out of the raw stormdata object and everywhere else
        stormcell_index = self.stormmap[frame_i][cell_i]
        self.stormdata = np.delete(self.stormdata, stormcell_index)
        self.stormmap[frame_i] = np.delete(self.stormmap[frame_i], cell_i)
        # Also need to decrement any indexes greater than stormcell_index
        for indexes in self.stormmap:
            indexes[indexes > stormcell_index] -= 1

    def save_stormdata(self, fname):
        storm_saver(fname, self.stormdata)

    # --- Viewer methods ---
    def change_frame(self, frame_delta):
        newi = self.i + frame_delta
        if newi >= self.data.shape[0]:
            newi = self.data.shape[0] - 1
        if newi < 0:
            newi = 0
        if newi != self.i:
            self._emit('frame_change', newi)
            self.i = newi
            self.fig.canvas.draw_idle()

    def update_radar_display(self, index):
        self.im.set_data(self.data[index])

    def display_stormcells(self, index):
        self.toggle_stormcells(self.i, False)
        self.toggle_stormcells(index, True)

    def enable_hide(self):
        self.disconnect_keymap()
        self._hidekey = self._lastkey.lower()
        self._hidecid = self.fig.canvas.mpl_connect('key_release_event',
                                                    self.release_hide)
        self._emit('hide', self.i)
        self.fig.canvas.draw_idle()

    def toggle_stormcells(self, i, visible=None):
        if visible is None:
            visible = not self.polygons[i].get_visible()
        self.polygons[i].set_visible(visible)

    def release_hide(self, event):
        if event.key.lower() == self._hidekey and self._hidecid is not None:
            self.fig.canvas.mpl_disconnect(self._hidecid)
            self._hidekey = None
            self._hidecid = None
            self.connect_keymap()
            self.toggle_stormcells(self.i, True)
            self.fig.canvas.draw_idle()

    def lolite_stormcell(self, inds):
        if inds is not None:
            frame_i, cell_i = inds
            lws = self.polygons[frame_i].get_linewidths()
            lws[cell_i] = 1
            self.polygons[frame_i].set_linewidths(lws)

    def hilite_stormcell(self, inds):
        if inds is not None:
            frame_i, cell_i = inds
            lws = self.polygons[frame_i].get_linewidths()
            lws[cell_i] = 4
            self.polygons[frame_i].set_linewidths(lws)

    # --- Selection/Deselection methods ---
    def select_stormcell(self, event):
        if event.artist not in self.polygons:
            return
        ind = event.ind[0]
        self._emit('deselect', self.selected)
        if (self.i, ind) != self.selected:
            self.selected = (self.i, ind)
            self._emit('select', self.selected)
        else:
            self.selected = None
        self.fig.canvas.draw_idle()

ctrl_sys = ControlSys(fig, im, data, polycolls, stormcells, stormmap)
plt.show()
