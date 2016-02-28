import matplotlib.pyplot as plt
from scipy.io import netcdf_file

ncf = netcdf_file('KTLX_20100510_22Z.nc')
data = ncf.variables['Reflectivity']
lats = ncf.variables['lat']
lons = ncf.variables['lon']
i = 0

fig, ax = plt.subplots(1, 1)
im = ax.imshow(data[i], origin='lower',
               extent=(lons[0], lons[-1], lats[0], lats[-1]),
               vmin=0, vmax=80, cmap='gist_ncar')
fig.colorbar(im)
plt.show()
