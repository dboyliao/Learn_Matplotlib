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
        ax.add_artist(Line2D(x, y, color='b'))

ax.set_xlim(-99, -95)
ax.set_ylim(33, 38)
plt.show()
