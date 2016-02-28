import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from tutorial import track_loader

tracks = track_loader('polygons.shp')

fig, ax = plt.subplots(1, 1)
for trkid, trk in tracks.items():
    x, y = zip(*trk)
    if trkid == -9:
        ax.scatter(x, y, color='r')
    else:
        ax.add_artist(Line2D(x, y, color='b', picker=2, lw=1))

class ControlSys:
    def __init__(self, fig):
        self.fig = fig
        self.selected = None
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

ctrl_sys = ControlSys(fig)
ax.set_xlim(-99, -95)
ax.set_ylim(33, 38)
plt.show()
