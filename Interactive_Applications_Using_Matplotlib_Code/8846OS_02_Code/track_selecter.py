import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from tutorial import track_loader

tracks = track_loader('polygons.shp')
# Filter out non-tracks (unassociated polygons given trackID of -9)
tracks = {tid: t for tid, t in tracks.items() if tid != -9}

fig, ax = plt.subplots(1, 1)
for trkid, trk in tracks.items():
    x, y = zip(*trk)
    ax.add_artist(Line2D(x, y, color='b', picker=2, lw=1))

def onpick(event):
    if not isinstance(event.artist, Line2D):
        return False
    else:
        if event.artist.get_linewidth() == 1:
            event.artist.set_linewidth(4)
        else:
            event.artist.set_linewidth(1)
        fig.canvas.draw_idle()
        return True
fig.canvas.mpl_connect('pick_event', onpick)

ax.set_xlim(-99, -95)
ax.set_ylim(33, 38)
plt.show()
