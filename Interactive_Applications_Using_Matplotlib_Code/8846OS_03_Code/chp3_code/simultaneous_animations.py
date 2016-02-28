import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.animation import FuncAnimation, ArtistAnimation
from tutorial import storm_loader
from scipy.io import netcdf_file

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
            indexes = indexes[np.argsort(stormdata['frame_index'][indexes])]
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


if __name__ == '__main__':
    stormcells = storm_loader('polygons.shp')
    ncf = netcdf_file('KTLX_20100510_22Z.nc')
    data = ncf.variables['Reflectivity']
    lats = ncf.variables['lat']
    lons = ncf.variables['lon']
    framecnt = data.shape[0]

    fig, ax = plt.subplots(1, 1)

    rad_disp = RadarDisplay(ax, lats, lons)
    fig.colorbar(rad_disp.im)
    trks = Tracks(ax)
    cells = Stormcells(ax, stormcells)
    cells.toggle_polygons(0, True)

    radanim = FuncAnimation(fig, lambda i, dat: rad_disp.update_display(dat[i]),
                            framecnt, fargs=(data,))
    trkanim = FuncAnimation(fig, trks.update_lines,
                            framecnt, fargs=(stormcells,))
    strmanim = ArtistAnimation(fig, [[p] for p in cells.polygons])

    plt.show()
