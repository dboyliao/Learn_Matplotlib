import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
from tutorial import track_loader, polygon_loader

tracks = track_loader('polygons.shp')
polygons = polygon_loader('polygons.shp', group='frame_index')

fig, ax = plt.subplots(1, 1)
for trkid, trk in tracks.items():
    x, y = zip(*trk)
    if trkid == -9:
        ax.scatter(x, y, color='r')
    else:
        ax.add_artist(Line2D(x, y, color='b', picker=2, lw=1))

poly_objs = []
for frame in sorted(polygons):
    frame_polys = []
    for poly in polygons[frame]:
        p = Polygon(poly, lw=3, fc='k', zorder=1,
                    ec='k', alpha=0.45, visible=(not frame))
        ax.add_artist(p)
        frame_polys.append(p)
    poly_objs.append(frame_polys)

class ControlSys:
    def __init__(self, fig, polygons):
        self.fig = fig
        self.selected = None
        self.polygons = polygons
        self.i = 0
        self.fig.canvas.mpl_connect('pick_event', self.onpick)
        self.fig.canvas.mpl_connect('key_press_event', self.keypress)

    def onpick(self, event):
        if not isinstance(event.artist, Line2D):
            return False
        else:
            if event.artist is not self.selected:
                # "Select" this track
                # But first, we need to de-select the previous selection
                if self.selected is not None:
                    self.selected.set_linewidth(1)
                event.artist.set_linewidth(4)
                self.selected = event.artist
            else:
                # "Deselect this track
                self.selected.set_linewidth(1)
                self.selected = None
            self.fig.canvas.draw_idle()
            return True

    def keypress(self, event):
        if event.key == 'd' and self.selected is not None:
            self.selected.remove()
            self.selected = None
            self.fig.canvas.draw_idle()
        else:
            previ = self.i
            if event.key == 'left' and self.i > 0:
                self.i -= 1
            elif event.key == 'right' and self.i < (len(self.polygons) - 1):
                self.i += 1
            if previ != self.i:
                for p in self.polygons[previ]:
                    p.set_visible(False)
                for p in self.polygons[self.i]:
                    p.set_visible(True)
            self.fig.canvas.draw_idle()


ctrl_sys = ControlSys(fig, poly_objs)
ax.set_xlim(-99, -95)
ax.set_ylim(33, 38)
plt.show()
