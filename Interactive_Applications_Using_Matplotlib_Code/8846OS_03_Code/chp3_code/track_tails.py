import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.animation import FuncAnimation
from tutorial import storm_loader

class Tracks(object):
    def __init__(self, ax, tails=None):
        self.tracks = None
        self.tails = tails
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
            if self.tails:
                mask = trackdata['frame_index'] >= (frame_index - self.tails)
                trackdata = trackdata[mask]
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
    fig, ax = plt.subplots(1, 1)
    trks = Tracks(ax, 3)
    ax.set_xlim(stormcells['xcent'].min(), stormcells['xcent'].max())
    ax.set_ylim(stormcells['ycent'].min(), stormcells['ycent'].max())
    trkanim = FuncAnimation(fig, trks.update_lines,
            stormcells['frame_index'].max() + 1, fargs=(stormcells,))
    plt.show()
