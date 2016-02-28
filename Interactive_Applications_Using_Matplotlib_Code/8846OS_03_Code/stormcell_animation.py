import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.animation import ArtistAnimation
import numpy as np
from tutorial import storm_loader

fig, ax = plt.subplots(1, 1)

stormcells = storm_loader('polygons.shp')
polycolls = []
for frame in range(np.max(stormcells['frame_index']) + 1):
    indexes = np.where(stormcells['frame_index'] == frame)[0]
    polygons = stormcells[indexes]['poly']
    pc = PolyCollection(polygons, lw=[1]*len(polygons),
                        facecolors='k', zorder=1, edgecolors='w', alpha=0.45,
                        picker=True)
    ax.add_collection(pc)
    polycolls.append([pc])

ax.autoscale(True)

anim = ArtistAnimation(fig, polycolls)

plt.show()
