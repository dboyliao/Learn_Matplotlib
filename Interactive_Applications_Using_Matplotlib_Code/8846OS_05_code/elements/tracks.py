import numpy as np
from matplotlib.collections import LineCollection

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

