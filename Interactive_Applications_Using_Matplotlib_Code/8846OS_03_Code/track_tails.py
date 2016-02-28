import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.animation import FuncAnimation
import numpy as np
from tutorial import storm_loader

class Tracks:
    def __init__(self, ax, stormcells, tails=None):
        self.tracks = None
        self.tails = tails
        self.update_trackmap(ax, stormcells)

    def update_trackmap(self, ax, stormcells):
        if self.tracks is not None:
            self.tracks.remove()
            self.tracks = None
        if self.tracks is None:
            self.tracks = LineCollection([])
            ax.add_collection(self.tracks)

        self.trackmap = []
        for trackid in range(np.max(stormcells['track_id']) + 1):
            indexes = np.where(stormcells['track_id'] == trackid)[0]
            # Makes sure the track segments are in chronological order
            indexes = indexes[np.argsort(stormcells['frame_index'][indexes])]
            self.trackmap.append(indexes)

    def update_frame(self, frame_index, stormcells):
        segments = []
        for trackid, indexes in enumerate(self.trackmap):
            trackdata = stormcells[indexes]
            trackdata = trackdata[trackdata['frame_index'] <= frame_index]
            if self.tails:
                mask = trackdata['frame_index'] > (frame_index - self.tails)
                trackdata = trackdata[mask]
            segments.append(zip(trackdata['xcent'], trackdata['ycent'])
                            or [(np.nan, np.nan)])
        self.tracks.set_segments(segments)

if __name__ == '__main__':
    stormcells = storm_loader('polygons.shp')
    framecnt = np.max(stormcells['frame_index']) + 1

    fig, ax = plt.subplots(1, 1)
    trks = Tracks(ax, stormcells, 4)
    ax.set_xlim(stormcells['xcent'].min(), stormcells['xcent'].max())
    ax.set_ylim(stormcells['ycent'].min(), stormcells['ycent'].max())

    anim = FuncAnimation(fig, trks.update_frame, framecnt, fargs=(stormcells,))
    plt.show()
