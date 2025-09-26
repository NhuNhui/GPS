import numpy as np
from pyproj import Transformer

# Input: observer geodetic position (WGS-84) and target angles + distance
lat_obs = 10.7400   # degrees
lon_obs = 106.5700  # degrees
alt_obs = 5.0       # meters

azimuth_deg = 60.0      # degrees, clockwise from North
elevation_deg = 10.0    # degrees, up from horizontal
distance = 2000.0       # meters

# Convert angles to radians
az = np.radians(azimuth_deg)
el = np.radians(elevation_deg)

# 1) Az/El -> ENU vector
E = distance * np.cos(el) * np.sin(az)  # East
N = distance * np.cos(el) * np.cos(az)  # North
U = distance * np.sin(el)               # Up
vec_enu = np.array([E, N, U])

# 2) Observer geodetic -> ECEF
to_ecef = Transformer.from_crs("epsg:4979", "epsg:4978", always_xy=True)
x_obs, y_obs, z_obs = to_ecef.transform(lon_obs, lat_obs, alt_obs)

# 3) ENU -> ECEF rotation at observer location
phi = np.radians(lat_obs)
lam = np.radians(lon_obs)
R = np.array([
    [-np.sin(lam), -np.sin(phi)*np.cos(lam),  np.cos(phi)*np.cos(lam)],
    [ np.cos(lam), -np.sin(phi)*np.sin(lam),  np.cos(phi)*np.sin(lam)],
    [        0.0,               np.cos(phi),               np.sin(phi)]
])

vec_ecef = R @ vec_enu

# 4) Target ECEF
x_tgt, y_tgt, z_tgt = x_obs + vec_ecef[0], y_obs + vec_ecef[1], z_obs + vec_ecef[2]

# 5) ECEF -> geodetic (WGS-84)
to_geo = Transformer.from_crs("epsg:4978", "epsg:4979", always_xy=True)
lon_tgt, lat_tgt, alt_tgt = to_geo.transform(x_tgt, y_tgt, z_tgt)

print(f"Target geodetic: lat={lat_tgt:.6f}°, lon={lon_tgt:.6f}°, alt={alt_tgt:.2f} m")
