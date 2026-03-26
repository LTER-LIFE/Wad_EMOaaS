#!/usr/bin/env python
"""
regrid_200m_to_500m_hotstart.py

Horizontally regrids a GETM/ERSEM restart file from 200 m to 500 m resolution.

Steps
-----
1.  Read 2-D geographic coordinates (lon/lat) from source and target topo.nc files.
2.  For every variable in the source restart file:
      - 0-D / 1-D  →  copy unchanged (time metadata, zax index array, etc.)
      - 2-D (yax, xax)              →  interpolate onto the 500 m grid
      - 3-D (zax, yax, xax)         →  interpolate layer-by-layer
3.  Write output as NETCDF3_CLASSIC (required by GETM hotstart reader).

Requirements
------------
  conda activate 3Dmodel_input_output_env   (python, netCDF4, numpy, scipy)

Usage
-----
  python regrid_200m_to_500m_hotstart.py
  # or edit the Settings section and run on the HPC cluster.
"""

from netCDF4 import Dataset
import numpy as np
from scipy.interpolate import griddata

# =============================================================================
# Settings  ---  adjust paths before running
# =============================================================================

# Combined 200 m restart file (10 layers, hydro + bio merged)
infname = '/export/lv9/user/qzhan/model_output/active_runs/boundaries/dws_200m_nwes/restart_dws200m_2015_01.nc'

# Output 500 m restart file
ofname  = '/export/lv9/user/qzhan/model_output/active_runs/boundaries/dws_200m_nwes/restart_dws500m_2015_01.nc'

# topo.nc for the SOURCE 200 m domain  (contains lonc/latc or lon/lat 2-D arrays)
src_topo_fname = '/export/lv9/user/qzhan/home/GETM_ERSEM_SETUPS/Input/topo/topo_adjusted_dws_200m_2009.nc'

# topo.nc for the TARGET 500 m domain
tgt_topo_fname = '/export/lv9/user/qzhan/home/GETM_ERSEM_SETUPS/Input/topo/topos2_dws_500m.nc'   # <-- update this path

# Name of the 2-D longitude / latitude variables inside topo.nc
# Common GETM names are 'lonc'/'latc' (T-grid centres) or 'lon'/'lat'.
lon_varname = 'lonc'
lat_varname = 'latc'

# Interpolation method passed to scipy.interpolate.griddata:
#   'nearest'  – safest for model restart (preserves physical ranges, no overshoot)
#   'linear'   – smooth but can extrapolate slightly outside the source hull
INTERP_METHOD = 'nearest'

# Fill value used for target points that fall outside the source domain
FILL_VALUE = 0.0

# =============================================================================
# Helper
# =============================================================================

def interp2d(src_lon, src_lat, src_data, tgt_lon, tgt_lat, method, fill_value):
    """Interpolate one 2-D layer from source to target grid.

    Parameters
    ----------
    src_lon, src_lat : 2-D arrays, shape (ny_src, nx_src)
    src_data         : 2-D array,  shape (ny_src, nx_src)
    tgt_lon, tgt_lat : 2-D arrays, shape (ny_tgt, nx_tgt)
    """
    # Flatten source grid to a list of (lon, lat) points
    src_pts  = np.column_stack((src_lon.ravel(), src_lat.ravel()))
    src_vals = src_data.ravel().astype(np.float64)

    # Mask out NaN / fill values from source before interpolating
    valid = np.isfinite(src_vals)
    if not np.any(valid):
        return np.full(tgt_lon.shape, fill_value)

    tgt_pts = np.column_stack((tgt_lon.ravel(), tgt_lat.ravel()))
    result  = griddata(src_pts[valid], src_vals[valid], tgt_pts,
                       method=method, fill_value=fill_value)
    return result.reshape(tgt_lon.shape)


# =============================================================================
# Main
# =============================================================================

print('Opening source topo:', src_topo_fname)
src_topo = Dataset(src_topo_fname, 'r')
src_lon  = np.array(src_topo.variables[lon_varname][:])   # (ny_src, nx_src)
src_lat  = np.array(src_topo.variables[lat_varname][:])
src_topo.close()
ny_src, nx_src = src_lon.shape
print(f'  Source grid  : {ny_src} x {nx_src}')

print('Opening target topo:', tgt_topo_fname)
tgt_topo = Dataset(tgt_topo_fname, 'r')
tgt_lon  = np.array(tgt_topo.variables[lon_varname][:])   # (ny_tgt, nx_tgt)
tgt_lat  = np.array(tgt_topo.variables[lat_varname][:])
tgt_topo.close()
ny_tgt, nx_tgt = tgt_lon.shape
print(f'  Target grid  : {ny_tgt} x {nx_tgt}')

print('Opening source restart:', infname)
infile = Dataset(infname, 'r', format='NETCDF4')

alldimnames = list(infile.dimensions.keys())
varnames    = list(infile.variables.keys())
print('Dimensions :', alldimnames)
print('Variables  :', varnames)

# ---- Build output file ------------------------------------------------------
print('Creating output file:', ofname)
outfile = Dataset(ofname, 'w', format='NETCDF3_CLASSIC')

# Re-create dimensions; replace xax/yax sizes with the target grid sizes.
for dname in alldimnames:
    dsize = len(infile.dimensions[dname])
    if dname == 'xax':
        dsize = nx_tgt
    elif dname == 'yax':
        dsize = ny_tgt
    # zax and any time/scalar dims keep their original size
    outfile.createDimension(dname, dsize)

# ---- Process variables ------------------------------------------------------
for varname in varnames:
    var      = infile.variables[varname]
    dimnames = var.dimensions
    datavals = np.array(var[:])
    dtype    = datavals.dtype.kind

    ndim = len(dimnames)
    print(f'  {varname:30s}  dims={dimnames}  shape={datavals.shape}', end='')

    # Identify dimensionality relative to spatial axes
    has_xax = 'xax' in dimnames
    has_yax = 'yax' in dimnames
    has_zax = 'zax' in dimnames

    if has_yax and has_xax and has_zax:
        # 3-D variable: (zax, yax, xax)  – interpolate layer by layer
        nz = datavals.shape[0]
        out = np.zeros((nz, ny_tgt, nx_tgt), dtype=np.float64)
        for iz in range(nz):
            out[iz] = interp2d(src_lon, src_lat, datavals[iz],
                               tgt_lon, tgt_lat, INTERP_METHOD, FILL_VALUE)
        out = out.astype(datavals.dtype)

    elif has_yax and has_xax and not has_zax:
        # 2-D variable: (yax, xax)
        out = interp2d(src_lon, src_lat, datavals,
                       tgt_lon, tgt_lat, INTERP_METHOD, FILL_VALUE)
        out = out.astype(datavals.dtype)

    elif varname == 'xax':
        # Replace with new 1-D index array for the 500 m grid
        out = np.arange(nx_tgt, dtype=datavals.dtype)

    elif varname == 'yax':
        out = np.arange(ny_tgt, dtype=datavals.dtype)

    else:
        # Scalar / 1-D / zax / time variables – copy unchanged
        out = datavals

    print(f'  →  {out.shape}')

    # Create variable (no chunksizes keyword needed for NETCDF3)
    outvar = outfile.createVariable(varname, dtype, dimnames)
    outvar[:] = out

    # Copy attributes (excluding NetCDF system attributes)
    for att in var.ncattrs():
        if att not in ('_FillValue', 'assignValue', 'getValue', 'typecode'):
            setattr(outvar, att, getattr(var, att))

# Copy global attributes
for att in infile.ncattrs():
    setattr(outfile, att, getattr(infile, att))

infile.close()
outfile.close()
print('Done.')
