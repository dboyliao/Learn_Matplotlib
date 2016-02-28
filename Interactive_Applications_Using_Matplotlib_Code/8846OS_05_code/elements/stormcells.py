import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.path import Path

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

        for indexes in self.create_stormmap(stormdata):
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


