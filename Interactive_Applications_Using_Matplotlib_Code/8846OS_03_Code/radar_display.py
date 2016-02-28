import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from scipy.io import netcdf_file

class RadarDisplay:
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


if __name__ == '__main__':
    ncf = netcdf_file('KTLX_20100510_22Z.nc')
    data = ncf.variables['Reflectivity']
    lats = ncf.variables['lat']
    lons = ncf.variables['lon']

    fig, ax = plt.subplots(1, 1)

    rad_disp = RadarDisplay(ax, lats, lons)
    fig.colorbar(rad_disp.im)

    anim = FuncAnimation(fig, lambda i, dat: rad_disp.update_display(dat[i]),
                         frames=data.shape[0], fargs=(data,))
    plt.show()
