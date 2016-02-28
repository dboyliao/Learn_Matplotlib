import matplotlib.pyplot as plt
from scipy.io import netcdf_file

ncf = netcdf_file('KTLX_20100510_22Z.nc')
data = ncf.variables['Reflectivity']
lats = ncf.variables['lat']
lons = ncf.variables['lon']

class ControlSys:
    def __init__(self, fig, data, im):
        self.data = data
        self.i = 0
        self.fig = fig
        self.im = im
        self.fig.canvas.mpl_connect('key_press_event', self.process_key)

    def process_key(self, event):
        if event.key == 'left' and self.i > 0:
            self.i -= 1
        elif event.key == 'right' and self.i < (self.data.shape[0] - 1):
            self.i += 1
        else:
            return

        self.im.set_data(self.data[self.i])
        self.fig.canvas.draw_idle()

fig, ax = plt.subplots(1, 1)
im = ax.imshow(data[0], origin='lower',
               extent=(lons[0], lons[-1], lats[0], lats[-1]),
               vmin=0, vmax=80, cmap='gist_ncar')
fig.colorbar(im)
ctrl_sys = ControlSys(fig, data, im)
plt.show()
