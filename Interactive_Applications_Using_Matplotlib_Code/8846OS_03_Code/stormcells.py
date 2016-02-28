import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.animation import ArtistAnimation
import numpy as np
from tutorial import storm_loader

class Stormcells:
    def __init__(self, ax, stormcells):
        self.storms = []
        self.update_stormmap(ax, stormcells)

    def update_stormmap(self, ax, stormcells):
        for strm in self.storms:
            strm.remove()
        self.storms = []
        self.stormmap = []

        for frame in range(np.max(stormcells['frame_index']) + 1):
            indexes = np.where(stormcells['frame_index'] == frame)[0]
            polygons = stormcells[indexes]['poly']

            pc = PolyCollection(polygons, lw=[1]*len(polygons), picker=True,
                    facecolors='k', zorder=1, edgecolors='w', alpha=0.45)
            ax.add_collection(pc)

            self.storms.append([pc])
            self.stormmap.append(indexes)

if __name__ == '__main__':
    fig, ax = plt.subplots(1, 1)
    stormcells = storm_loader('polygons.shp')
    cells = Stormcells(ax, stormcells)
    ax.autoscale(True)

    anim = ArtistAnimation(fig, cells.storms)
    plt.show()
