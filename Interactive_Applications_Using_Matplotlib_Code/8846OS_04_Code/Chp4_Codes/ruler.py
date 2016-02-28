from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from mpl_toolkits.basemap import Basemap, pyproj

def distance(evnt_click, evnt_release):
    g = pyproj.Geod(ellps='WGS84')
    _, _, dist = g.inv(evnt_click.xdata, evnt_click.ydata,
                       evnt_release.xdata, evnt_release.ydata)
    print("(%f, %f) to (%f, %f): %f km" %
            (evnt_click.xdata, evnt_click.ydata,
             evnt_release.xdata, evnt_release.ydata, dist / 1000.0))

if __name__ == '__main__':
    fig, ax = plt.subplots(1, 1)
    bm = Basemap(projection='cyl', resolution='l',
                 llcrnrlon=-130, llcrnrlat=25,
                 urcrnrlon=-60, urcrnrlat=55)
    bm.drawstates(ax=ax)
    bm.drawcountries(ax=ax)
    bm.drawcoastlines(ax=ax)
    rs = RectangleSelector(ax, distance, drawtype='line',
                           minspanx=0.001, minspany=0.001)
    plt.show()
