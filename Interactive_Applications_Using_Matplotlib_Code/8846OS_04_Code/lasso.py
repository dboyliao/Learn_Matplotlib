from __future__ import print_function
from collections import OrderedDict
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import netcdf_file
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib import widgets
from tutorial import storm_loader, storm_saver

def calc_area(verts):
    """
    Calculate an approximate area in square km of a polygon with
    vertices as a list of lon/lat pairs in degrees. Assumes spherical Earth.
    Must have at least 3 vertices to make a polygon.

    """
    N = len(verts)
    verts = np.deg2rad(verts)
    if N < 3 :
        return 0.0

    RadSq = 6371.0**2
    area = 0.0
    area -= ((verts[1, 0] - verts[-2, 0]) * np.sin(verts[0, 1]))
    for i in xrange(1, N - 1):
        area -= ((verts[i + 1, 0] - verts[i - 1, 0]) * np.sin(verts[i, 1]))
    return 0.5 * RadSq * area

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


class Stormcells(object):
    def __init__(self, ax, stormdata):
        self.polygons = []
        self.create_polygons(ax, stormdata)
        self._visible = True

    @staticmethod
    def create_stormmap(stormdata):
        stormmap = [np.where(stormdata['frame_index'] == frame)[0]
                    for frame in range(np.max(stormdata['frame_index']) + 1)]
        return stormmap

    def remove_polygons(self):
        for strm in self.polygons:
            strm.remove()
        self.polygons = []

    def create_polygons(self, ax, stormdata):
        # Clear any previously existing polygons
        self.remove_polygons()

        for indexes in self.create_stormmap(stormcells):
            polygons = stormdata[indexes]['poly']
            pc = PolyCollection(polygons, lw=[1]*len(polygons), picker=True,
                    facecolors='k', zorder=1, edgecolors='w', alpha=0.45,
                    visible=False)
            ax.add_collection(pc)
            self.polygons.append(pc)

    def delete_polygon(self, inds):
        frame_i, cell_i = inds
        paths = self.polygons[frame_i].get_paths()
        paths.pop(cell_i)
        lws = self.polygons[frame_i].get_linewidths()
        lws.pop(cell_i)

    def add_polygon(self, celldata):
        frame_i, verts = celldata
        paths = self.polygons[frame_i].get_paths()
        paths.append(Path(verts, closed=True))
        lws = self.polygons[frame_i].get_linewidths()
        lws.append(1)

    def toggle_polygons(self, frame_index, visible=None):
        if visible is None:
            visible = not self.polygons[frame_index].get_visible()
        self.polygons[frame_index].set_visible(visible and self._visible)

    def get_visible(self):
        return self._visible

    def set_visible(self, visible):
        self._visible = bool(visible)

    def lolite_polygon(self, inds):
        self.hilite_polygon(inds, 1)

    def hilite_polygon(self, inds, lw=4):
        if inds is not None:
            frame_i, cell_i = inds
            lws = self.polygons[frame_i].get_linewidths()
            lws[cell_i] = lw
            self.polygons[frame_i].set_linewidths(lws)

class Tracks(object):
    def __init__(self, ax):
        self.tracks = None
        self.initialize_lines(ax)

    @staticmethod
    def create_trackmap(stormdata):
        trackmap = []
        for trackid in range(np.max(stormdata['track_id']) + 1):
            indexes = np.where(stormdata['track_id'] == trackid)[0]
            # Makes sure the track segments are in chronological order
            indexes = indexes[np.argsort(stormcells['frame_index'][indexes])]
            trackmap.append(indexes)
        return trackmap

    def remove_lines(self):
        if self.tracks is not None:
            self.tracks.remove()
            self.tracks = None

    def initialize_lines(self, ax):
        self.remove_lines()
        self.tracks = LineCollection([])
        ax.add_collection(self.tracks)

    def update_lines(self, frame_index, stormdata):
        segments = []
        for indexes in self.create_trackmap(stormdata):
            trackdata = stormdata[indexes]
            trackdata = trackdata[trackdata['frame_index'] <= frame_index]
            # There must always be something in a track, even it it is NaNs.
            segments.append(zip(trackdata['xcent'], trackdata['ycent'])
                            or [(np.nan, np.nan)])
        self.tracks.set_segments(segments)

    def lolite_line(self, indx):
        self.hilite_line(indx, 1)

    def hilite_line(self, indx, lw=4):
        if indx is not None:
            lws = self.tracks.get_linewidths()
            lws[indx] = lw
            self.tracks.set_linewidths(lws)


class PickControl:
    def __init__(self, fig):
        self.fig = fig
        self._pickers = []
        self._pickcids = []

    def connect_picks(self):
        for i, picker in enumerate(self._pickers):
            if self._pickcids[i] is None:
                cid = self.fig.canvas.mpl_connect('pick_event', picker)
                self._pickcids[i] = cid

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

class ButtonControl:
    def __init__(self, fig, width, height):
        self.fig = fig
        # Give us some room along the top
        fig.subplots_adjust(top=1-height*2)
        self._buttonwidth = width
        self._buttonheight = height
        self._buttonmap = {}

    def connect_buttonmap(self):
        for text, (cid, func, button) in self._buttonmap.items():
            if cid is None:
                cid = button.on_clicked(func)
                self._buttonmap[text] = (cid, func, button)

    def disconnect_buttonmap(self):
        for text, (cid, func, button) in self._buttonmap.items():
            if cid is not None:
                button.disconnect(cid)
                self._buttonmap[text] = (None, func, button)

    def add_button_action(self, text, action_func):
        if not callable(action_func):
            raise ValueError("Invalid button action. Button '%s''s"
                             " action function is not a callable" % text)
        if text in self._buttonmap:
            raise ValueError("Button '%s' is already a button" % text)
        ax = self.fig.add_axes([len(self._buttonmap) * self._buttonwidth,
                                0.99 - self._buttonheight,
                                self._buttonwidth, self._buttonheight])
        button = widgets.Button(ax, text)
        # Swallow the event parameter. We don't need it for these buttons
        func = lambda event: action_func()
        cid = button.on_clicked(func)
        self._buttonmap[text] = (cid, func, button)

def build_progress_bar(fig, lastframe, height):
    # Give us some room along the bottom
    fig.subplots_adjust(bottom=2*height)
    barax = fig.add_axes([0.08, 0.005, 0.78, height])
    bar = widgets.Slider(barax, 'Time', 0, lastframe, valinit=0,
                         valfmt='%d of '+str(lastframe))
    return bar

def build_check_buttons(fig, width):
    # Give us some room along the right
    fig.subplots_adjust(right=1-width)
    boxax = fig.add_axes([0.99 - width, 0.8, width, 0.1])
    checks = widgets.CheckButtons(boxax, ('Radar', 'Polys', 'Tracks'),
                                  [True]*3)
    return checks

def build_radio_buttons(fig, height):
    # Give us some room along the top
    fig.subplots_adjust(top=1-height)
    button_ax = fig.add_axes([0.85, 1 - height, 0.14, height])
    buttons = widgets.RadioButtons(button_ax, ('Selection', 'Outline'))
    # Compatibility layer (this method was not added until v1.5)
    if not hasattr(buttons, 'set_active'):
        def set_active(index):
            if 0 > index >= len(buttons.labels):
                raise ValueError("Invalid RadioButton index: %d" % index)

            for i, p in enumerate(buttons.circles):
                if i == index:
                    color = buttons.activecolor
                else:
                    color = buttons.ax.get_axis_bgcolor()
                p.set_facecolor(color)

            if buttons.drawon:
                buttons.ax.figure.canvas.draw()

            if not buttons.eventson:
                return
            for cid, func in buttons.observers.items():
                func(buttons.labels[index].get_text())
        buttons.set_active = set_active
    return buttons

class ControlSys(KeymapControl, PickControl, ButtonControl):
    def __init__(self, fig, raddisp, data, polygons, lines, stormdata):
        self.fig = fig
        self.raddisp = raddisp
        self.data = data
        self.i = 0
        self.selected = None
        self.polygons = polygons
        self.lines = lines
        self.stormdata = stormdata
        self.stormmap = polygons.create_stormmap(stormdata)
        self._hidekey = None
        self._hidecid = None
        KeymapControl.__init__(self, fig)
        PickControl.__init__(self, fig)
        ButtonControl.__init__(self, fig, 0.1, 0.05)
        self._progress_bar = build_progress_bar(fig, data.shape[0] - 1, 0.02)
        self._toggle_buttons = build_check_buttons(fig, 0.1)
        self._mode_buttons = build_radio_buttons(fig, 0.1)
        self._mode = 'Selection'
        self._lasso = None

        self._connect('frame_change', self.update_radar_display)
        self._connect('frame_change', self.display_stormcells)
        self._connect('frame_change', self.update_track_display)
        self._connect('frame_change', self.update_progress_bar)
        self._connect('select', self.polygons.hilite_polygon)
        self._connect('deselect', self.polygons.lolite_polygon)
        self._connect('hide', self.polygons.toggle_polygons)
        self._connect('delete', self.polygons.delete_polygon)
        self._connect('delete', self.delete_stormcell)
        self._connect('create', self.polygons.add_polygon)
        self._connect('create', self.add_stormcell)
        self._connect('save', lambda x: self.save_stormdata('polygons_new.shp'))
        self._connect('help', lambda x: self.display_help_menu())
        self._connect('button_press_event', self._start_stormcell)

        self._mode_buttons.on_clicked(self.set_mode)
        self._toggle_buttons.on_clicked(self.toggle_visibility)
        self._mode_buttons.on_clicked(self.set_mode)
        self.add_key_action('s', 'Selection mode',
                            lambda : self.set_mode('Selection'))
        self.add_key_action('o', 'Outline mode',
                            lambda : self.set_mode('Outline'))
        self._progress_bar.on_changed(
                lambda frame: self.change_frame(int(frame) - self.i))
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

        self.add_button_action('|<', lambda : self.change_frame(-1))
        self.add_button_action('>|', lambda : self.change_frame(1))
        self.add_button_action('Del', self.delete_selected)
        self.add_button_action('Save', lambda : self._emit('save', None))
        self.add_button_action('Help', lambda : self._emit('help', None))

        self.add_pick_action(self.select_stormcell)

    def _emit(self, event, eventdata):
        self.fig.canvas.callbacks.process(event, eventdata)

    def _connect(self, event, callback):
        self.fig.canvas.mpl_connect(event, callback)

    def set_mode(self, mode):
        if mode != self._mode:
            self._mode_buttons.eventson = False
            if mode == 'Selection':
                self.connect_picks()
                self._mode_buttons.set_active(0)
            elif mode == 'Outline':
                self.disconnect_picks()
                self._mode_buttons.set_active(1)
            else:
                self._mode_buttons.eventson = True
                raise ValueError("Invalid mode value: %s" % mode)
            self._mode_buttons.eventson = True
            self._mode = mode

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

    def delete_stormcell(self, inds):
        frame_i, cell_i = inds
        # Take it out of the raw stormdata object and everywhere else
        stormcell_index = self.stormmap[frame_i][cell_i]
        self.stormdata = np.delete(self.stormdata, stormcell_index)
        self.stormmap[frame_i] = np.delete(self.stormmap[frame_i], cell_i)
        # Also need to decrement any indexes greater than stormcell_index
        for indexes in self.stormmap:
            indexes[indexes > stormcell_index] -= 1

    def add_stormcell(self, celldata):
        frame_i, verts = celldata
        stormcell_index = np.max(self.stormdata['feat_id']) + 1
        xcent, ycent = np.mean(verts, axis=0)
        newcell = np.array([(xcent, ycent, frame_i, np.nan, calc_area(verts),
                            stormcell_index, -9, np.array(verts))],
                           dtype=storm_dtype)
        self.stormdata = np.append(self.stormdata, newcell)
        self.stormmap[frame_i] = np.append(self.stormmap[frame_i],
                                           stormcell_index)

    def save_stormdata(self, fname):
        storm_saver(fname, self.stormdata)

    def _start_stormcell(self, event):
        if self.fig.canvas.widgetlock.locked():
            return
        if event.inaxes is not self.raddisp.im.get_axes():
            return
        if self._mode != 'Outline':
            return
        self._lasso = widgets.Lasso(event.inaxes, (event.xdata, event.ydata),
                                    self._finish_stormcell)
        self.fig.canvas.widgetlock(self._lasso)

    def _finish_stormcell(self, verts):
        if len(verts) > 2:
            self._emit('create', (self.i, verts))
        self.fig.canvas.widgetlock.release(self._lasso)
        self._lasso = None
        self.fig.canvas.draw_idle()

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
        self.raddisp.update_display(self.data[index])

    def update_track_display(self, index):
        self.lines.update_lines(index, self.stormdata)

    def update_progress_bar(self, index):
        self._progress_bar.eventson = False
        self._progress_bar.set_val(index)
        self._progress_bar.eventson = True

    def display_stormcells(self, index):
        self.polygons.toggle_polygons(self.i, False)
        self.polygons.toggle_polygons(index, True)

    def enable_hide(self):
        self.disconnect_keymap()
        self._hidekey = self._lastkey.lower()
        self._hidecid = self.fig.canvas.mpl_connect('key_release_event',
                                                    self.release_hide)
        self._emit('hide', self.i)
        self.fig.canvas.draw_idle()

    def release_hide(self, event):
        if event.key.lower() == self._hidekey and self._hidecid is not None:
            self.fig.canvas.mpl_disconnect(self._hidecid)
            self._hidekey = None
            self._hidecid = None
            self.connect_keymap()
            self.polygons.toggle_polygons(self.i, True)
            self.fig.canvas.draw_idle()

    def toggle_visibility(self, item):
        if item == 'Radar':
            self.raddisp.im.set_visible(not self.raddisp.im.get_visible())
        elif item == 'Polys':
            self.polygons.set_visible(not self.polygons.get_visible())
            self.polygons.toggle_polygons(self.i, self.polygons.get_visible())
        elif item == 'Tracks':
            self.lines.tracks.set_visible(not self.lines.tracks.get_visible())
        else:
            raise ValueError("Invalid name %s for visibility toggling" % item)
        self.fig.canvas.draw_idle()

    # --- Selection/Deselection methods ---
    def select_stormcell(self, event):
        if event.artist not in self.polygons.polygons:
            return
        ind = event.ind[0]
        self._emit('deselect', self.selected)
        if (self.i, ind) != self.selected:
            self.selected = (self.i, ind)
            self._emit('select', self.selected)
        else:
            self.selected = None
        self.fig.canvas.draw_idle()

if __name__ == '__main__':
    from matplotlib.animation import FuncAnimation

    ncf = netcdf_file('KTLX_20100510_22Z.nc')
    data = ncf.variables['Reflectivity']
    lats = ncf.variables['lat']
    lons = ncf.variables['lon']
    stormcells = storm_loader('polygons.shp')

    fig, ax = plt.subplots(1, 1)
    raddisp = RadarDisplay(ax, lats, lons)
    raddisp.update_display(data[0])
    fig.colorbar(raddisp.im)
    polycolls = Stormcells(ax, stormcells)
    linecoll = Tracks(ax)

    # Turn on the first frame's polygons
    polycolls.toggle_polygons(0, True)
    ax.autoscale(True)

    ctrl_sys = ControlSys(fig, raddisp, data, polycolls, linecoll, stormcells)
    #anim = FuncAnimation(fig, lambda _: ctrl_sys.change_frame(1),
    #                     frames=data.shape[0], repeat=False)
    #anim.save('storms_with_tracks.gif', writer='imagemagick')
    plt.show()

