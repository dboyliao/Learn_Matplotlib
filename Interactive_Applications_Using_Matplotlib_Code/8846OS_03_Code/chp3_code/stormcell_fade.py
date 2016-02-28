import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.animation import FuncAnimation
from tutorial import storm_loader

class Stormcells(object):
    def __init__(self, ax, stormdata):
        self.polygons = []
        self.create_polygons(ax, stormdata)

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

    def toggle_polygons(self, frame_index, visible=None):
        if visible is None:
            visible = not self.polygons[frame_index].get_visible()
        self.polygons[frame_index].set_visible(visible)

    def lolite_polygon(self, inds):
        self.hilite_polygon(inds, 1)

    def hilite_polygon(self, inds, lw=4):
        if inds is not None:
            frame_i, cell_i = inds
            lws = self.polygons[frame_i].get_linewidths()
            lws[cell_i] = lw
            self.polygons[frame_i].set_linewidths(lws)

if __name__ == '__main__':
    stormcells = storm_loader('polygons.shp')
    frameCnt = stormcells['frame_index'].max() + 1

    fig, ax = plt.subplots(1, 1)
    cells = Stormcells(ax, stormcells)
    ax.autoscale(True)

    polys = [p for p in cells.polygons]
    for p in polys:
        p.set_visible(True)
        p.set_alpha(0.0)

    def update(frame, polys):
        for i, p in enumerate(polys):
            alpha = 0.0 if i > frame else 1.0 / ((frame - i + 1)**2)
            p.set_alpha(alpha)

    strmanim = FuncAnimation(fig, update, frameCnt, fargs=(polys,))
    plt.show()
