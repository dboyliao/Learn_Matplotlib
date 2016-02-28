from mpl_toolkits.basemap import shapefile
from collections import defaultdict
from itertools import groupby, izip
import numpy as np

storm_dtype = [('xcent', 'f'), ('ycent', 'f'), ('frame_index', 'i'),
               ('frame_time', 'f'), ('feat_size', 'f'),
               ('feat_id', 'i'), ('track_id', 'i'), ('poly', 'O')]

def storm_loader(filename):
    """
    Return a flat table of data. Each row is a feature.
    Columns are

    xcent, ycent, frame_index, frame_time, feat_size, feat_id, track_id
    and then a Nx2 array of polygon vertices ('poly').

    """
    shp = shapefile.Reader(filename)
    storms = np.array([tuple(record) + (np.array(poly.points),)
                       for record, poly in
                       izip(shp.iterRecords(), shp.iterShapes())],
                      dtype=storm_dtype)
    return storms

def storm_saver(filename, storms):
    """
    Save a numpy structured array (or, at least a list of numpy
    elements with the proper dtypes) where each row is a feature.
    Columns are

    xcent, ycent, frame_index, frame_time, feat_size, feat_id, track_id
    and then a Nx2 array of polygon vertices ('poly').
    """
    shp = shapefile.Writer(shapeType=shapefile.POLYGON)
    shp.field('x', 'N', decimal=6)
    shp.field('y', 'N', decimal=6)
    shp.field('frameindx', 'N')
    shp.field('frametime', 'N', decimal=4)
    shp.field('size', 'N', decimal=2)
    shp.field('cornerid', 'N')
    shp.field('trackid', 'N')
    for storm in storms:
        shp.record(storm['xcent'], storm['ycent'], storm['frame_index'],
                   storm['frame_time'], storm['feat_size'], storm['feat_id'],
                   storm['track_id'])
        if storm['poly'] is not None and len(storm['poly']) > 0:
            shp.poly([storm['poly'].tolist()])
        else:
            shp.null()
    if filename.endswith('.shp'):
        filename = filename[:-4]
    shp.save(filename)

def track_loader(filename, group='track_id'):
    storms = storm_loader(filename)
    tracks = defaultdict(list)
    for key, items in groupby(storms, lambda x: x[group]):
        for storm in items:
            tracks[key].append((storm['xcent'], storm['ycent']))
    return tracks

def polygon_loader(filename, group='frame_index'):
    storms = storm_loader(filename)
    polygons = defaultdict(list)
    for key, items in groupby(storms, lambda x: x[group]):
        for storm in items:
            polygons[key].append(storm['poly'])
    return polygons

def calc_area(verts):
    """
    Calculate an approximate area in square km of a polygon with
    vertices as a list of lon/lat pairs in degrees. Assumes spherical Earth.
    Must have at least 3 vertices to make a polygon.

    """
    N = len(verts)
    verts = np.deg2rad(verts)
    if N < 3 :
        return 0.0

    RadSq = 6371.0**2
    area = 0.0
    area -= ((verts[1, 0] - verts[-2, 0]) * np.sin(verts[0, 1]))
    for i in xrange(1, N - 1):
        area -= ((verts[i + 1, 0] - verts[i - 1, 0]) * np.sin(verts[i, 1]))
    return 0.5 * RadSq * area

