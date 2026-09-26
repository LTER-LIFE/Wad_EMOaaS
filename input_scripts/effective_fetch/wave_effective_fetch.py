#!/usr/bin/env python3
"""Effective-fetch input file for the GETM-BFM Silt wave scheme.

Standalone tool: needs only numpy, scipy, xarray and netCDF4.

Builds the file named by `wave_fetch_file` in getm_bio.inp (&getm_bfm_wave_nml),
used by Silt.nml wave_method 2, the effective-fetch scheme. The fields are
computed on the GETM bathymetry file itself, so they have exactly the
dimensions GETM reads, with bathymetry.adjust applied as GETM applies it.

Method
------
From every wet cell, rays are marched toward each of 36 geographic bearings
(0, 10, ..., 350 deg; the direction the wind blows FROM). A ray stops at land
or at the first cell with still-water depth below

    h_eff = min(h_block, h_0 - delta)

where h_0 is the depth of the origin cell. The h_0 - delta term lets a ray that
starts on a flat run over flats of similar depth. A ray that leaves the grid
through an open edge reaches open sea and gets max_fetch; through a closed edge
it is blocked there. Each bearing is the cosine-weighted mean of n_sub sub-rays
over +-half_sector deg. Ray directions follow the grid convergence `convc`
(compass bearing of grid north) of every cell.

Variables, all (yc, xc), metres; the three fields wave_method 2 reads:
  fetch_dir_000 ... fetch_dir_350  directional fetch, h_block = --h-dir
  fetch_exp                        direction mean, blocked only by water
                                   shallower than h_0 - delta
  fetch_tp                         direction mean, h_block = --h-tp
Bearings are geographic; BFM rotates the grid-relative model wind with convc,
so the file does not depend on how the wind is given.

Land cells (H <= Hland, -10 m in GETM) hold the missing value -1. GETM stops
with 'missing or negative fetch' if a wet column meets it, so a file that does
not match the model mask cannot pass unnoticed.

Defaults are the values calibrated for the Dutch Wadden Sea 500 m setup
(h_dir 2.5 m, h_tp -0.25 m, delta 0.5 m, 200 km open-sea fetch).

Grids: GETM grid_type 1 (Cartesian) with uniform dx, dy. Without convc in the
topo file grid north is taken as true north (--grid-north to override), as
GETM does for the wind.

Examples
--------
    python wave_effective_fetch.py topo.nc -a bathymetry.adjust -o effective_fetch.nc
    python wave_effective_fetch.py topo.nc --open-edges WN --h-dir 5.0
Then in Silt.nml:
    wave_method=2
Then in getm_bio.inp:
    &getm_bfm_wave_nml
      wave_fetch_file='Input/effective_fetch.nc'
    /
"""
import argparse
import os
import sys
import time

import numpy as np
import xarray as xr
from scipy import ndimage

N_DIR = 36                # fixed: BFM ModuleSilt NBEAR_FETCH, variable names fetch_*_000..350
STEP = 0.5                # march step, in grid cells
H_LAND = -10.0            # GETM Hland: cells with H <= H_LAND are land
LAND_VALUE = -1.0         # missing value written on land cells
LOCAL = np.inf            # h_block for fetch_exp: blocked only by h < h_0 - delta

DEFAULTS = dict(h_dir=2.5, h_tp=-0.25, delta=0.5, max_fetch=200e3,
                half_sector=30.0, n_sub=7, open_edges="WESN")


# --------------------------------------------------------------------------- input

def read_adjust(fn):
    """GETM bathymetry.adjust: a count line, then 'il jl ih jh value' (1-based i, j).
    Comment lines start with '#' or '!'."""
    rows = []
    if not fn:
        return rows
    n = None
    with open(fn) as fh:
        for line in fh:
            s = line.split("#")[0].split("!")[0].strip()
            if not s:
                continue
            if n is None:
                n = int(s.split()[0])
                continue
            p = s.split()
            rows.append((int(p[0]), int(p[1]), int(p[2]), int(p[3]), float(p[4])))
    return rows[:n]


def read_topo(topo, adjust=None, grid_north=None):
    """Bathymetry (NaN on land), convc (deg), dx, dy and the dataset."""
    ds = xr.open_dataset(topo, mask_and_scale=False)
    if "grid_type" in ds and int(ds.grid_type) != 1:
        sys.exit(f"{topo}: grid_type {int(ds.grid_type)} not supported "
                 "(only Cartesian grids, grid_type 1)")
    bathy = ds.bathymetry.values.astype(float)
    bathy[~np.isfinite(bathy)] = H_LAND

    for il, jl, ih, jh, x in read_adjust(adjust):
        print(f"bathymetry.adjust: i {il}-{ih}, j {jl}-{jh} -> {x}")
        bathy[jl - 1:jh, il - 1:ih] = x
    bathy[bathy <= H_LAND + 1e-6] = np.nan                  # same mask as GETM az

    dx, dy = grid_spacing(ds)
    print(f"grid {bathy.shape[1]} x {bathy.shape[0]} (xc x yc), dx {dx:g} m, dy {dy:g} m, "
          f"{np.isfinite(bathy).sum()} wet cells")

    if "convc" in ds:
        convc = ds.convc.values.astype(float)
        src = "convc"
    else:
        # GETM itself uses convc = 0 without it, also to rotate the wind for BFM,
        # so the fetch rays must use the same orientation to stay consistent
        g = 0.0 if grid_north is None else float(grid_north)
        convc = np.full(bathy.shape, g)
        src = f"no convc in topo file, grid north = {g:g} deg"
        print(f"WARNING: no convc in {topo}; grid north taken as {g:g} deg. GETM then also "
              "uses convc = 0 for the wind: add convc to the topo file if the grid is rotated.")
    convc = np.where(np.isfinite(convc), convc, np.nanmean(convc))
    print(f"grid orientation ({src}): convc {convc.min():.2f} to {convc.max():.2f} deg")
    return bathy, convc, dx, dy, ds, src


def grid_spacing(ds):
    def scalar(v):
        if v in ds:
            x = float(ds[v].values)
            if np.isfinite(x) and 0 < x < 1e6:
                return x
        return None

    dx, dy = scalar("dx"), scalar("dy")
    for name, coord in (("dx", "xc"), ("dy", "yc")):
        if (dx if name == "dx" else dy) is None:
            d = np.diff(ds[coord].values.astype(float))
            if not np.allclose(d, d[0], rtol=1e-3):
                sys.exit(f"{coord} is not uniformly spaced; give {name} in the topo file")
            if name == "dx":
                dx = abs(d[0])
            else:
                dy = abs(d[0])
    return dx, dy


# --------------------------------------------------------------------------- fetch

def grid_fetch(bathy, convc, dx, dy, h_blocks, delta, max_fetch, half_sector, n_sub,
               open_edges, verbose=True):
    """Sector-mean effective fetch on every wet cell for several h_block at once.

    Returns bearings and {h_block: array (N_DIR, nj, ni)} in metres, NaN on land.
    Each sub-ray is marched once for all cells and all thresholds.
    """
    nj, ni = bathy.shape
    jj, ii = np.where(np.isfinite(bathy))
    n = len(jj)
    h0 = bathy[jj, ii]
    H = np.array([np.minimum(h, h0 - delta) for h in h_blocks])      # (T, n)
    cv = convc[jj, ii]

    ds = STEP * min(dx, dy)                   # march step, m
    n_steps = int(max_fetch / ds)
    bearings = np.arange(N_DIR) * 360.0 / N_DIR
    offs = np.linspace(-half_sector, half_sector, n_sub)
    w = np.cos(np.radians(offs))
    w /= w.sum()

    out = {h: np.full((N_DIR, nj, ni), np.nan, dtype=np.float32) for h in h_blocks}
    t0 = time.time()
    for d, b0 in enumerate(bearings):
        acc = np.zeros((len(h_blocks), n))
        for o, wt in zip(offs, w):
            a = np.radians((b0 + o) % 360.0 - cv)       # bearing relative to grid north
            di = np.sin(a) * ds / dx                     # cells per step along i (grid east)
            dj = np.cos(a) * ds / dy                     # cells per step along j (grid north)
            first = np.full((len(h_blocks), n), n_steps, dtype=np.int32)
            alive = np.ones((len(h_blocks), n), dtype=bool)
            any_alive = np.ones(n, dtype=bool)
            for k in range(1, n_steps + 1):
                idx = np.flatnonzero(any_alive)
                if not len(idx):
                    break
                fi = np.rint(ii[idx] + di[idx] * k).astype(np.int32)
                fj = np.rint(jj[idx] + dj[idx] * k).astype(np.int32)
                west, east, south, north = fi < 0, fi >= ni, fj < 0, fj >= nj
                outside = west | east | south | north
                closed = np.zeros_like(outside)
                for flag, m in (("W", west), ("E", east), ("S", south), ("N", north)):
                    if flag not in open_edges:
                        closed |= m
                cl = idx[closed]
                first[:, cl] = np.where(alive[:, cl], k, first[:, cl])   # closed edge: blocked
                alive[:, idx[outside]] = False                          # open edge: max_fetch
                ins = idx[~outside]
                val = bathy[fj[~outside], fi[~outside]]
                hit = alive[:, ins] & (np.isnan(val)[None, :] | (val[None, :] < H[:, ins]))
                tt, cc = np.nonzero(hit)
                first[tt, ins[cc]] = k
                alive[tt, ins[cc]] = False
                any_alive = alive.any(0)
            acc += wt * np.minimum(first * ds, max_fetch)
        for t, h in enumerate(h_blocks):
            out[h][d, jj, ii] = acc[t]
        if verbose:
            print(f"  bearing {b0:5.1f}  {time.time() - t0:6.0f} s", flush=True)
    return bearings, out


def fill_nearest(a):
    """Replace NaN by the value of the nearest finite cell."""
    bad = ~np.isfinite(a)
    if not bad.any():
        return a
    idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
    return a[tuple(idx)]


# --------------------------------------------------------------------------- output

def build(topo, out, adjust=None, h_dir=DEFAULTS["h_dir"], h_tp=DEFAULTS["h_tp"],
          delta=DEFAULTS["delta"], max_fetch=DEFAULTS["max_fetch"],
          half_sector=DEFAULTS["half_sector"], n_sub=DEFAULTS["n_sub"],
          open_edges=DEFAULTS["open_edges"], land="missing", grid_north=None,
          verbose=True):
    open_edges = open_edges.upper()
    bathy, convc, dx, dy, ds, orient = read_topo(topo, adjust, grid_north)
    wet = np.isfinite(bathy)

    thresholds = [h_dir, LOCAL]
    thresholds += [h_tp] if h_tp not in thresholds else []
    print(f"marching {N_DIR} bearings x {n_sub} sub-rays, h_block {thresholds}, "
          f"open edges '{open_edges}'")
    bearings, f = grid_fetch(bathy, convc, dx, dy, thresholds, delta, max_fetch,
                             half_sector, n_sub, open_edges, verbose)

    def finish(a):
        a = np.array(a, dtype=float)
        if land == "nearest":
            a = fill_nearest(a)
        else:
            a[~wet] = np.nan                  # written as LAND_VALUE through _FillValue
        return a.astype(np.float32)

    def dirmean(a):
        m = np.full(a.shape[1:], np.nan)
        m[wet] = a[:, wet].mean(axis=0)
        return m

    data = {}
    for k, b in enumerate(bearings):
        data[f"fetch_dir_{int(round(b)):03d}"] = xr.DataArray(
            finish(f[h_dir][k]), dims=("yc", "xc"),
            attrs=dict(units="m", long_name=f"effective fetch, wind from {b:g} deg",
                       bearing_from_deg=float(b), h_block=h_dir, delta=delta))
    data["fetch_exp"] = xr.DataArray(
        finish(dirmean(f[LOCAL])), dims=("yc", "xc"),
        attrs=dict(units="m", long_name="direction-mean exposure fetch",
                   h_block="local depth - delta", delta=delta))
    data["fetch_tp"] = xr.DataArray(
        finish(dirmean(f[h_tp])), dims=("yc", "xc"),
        attrs=dict(units="m", long_name="direction-mean period fetch",
                   h_block=h_tp, delta=delta))
    for v in ("latc", "lonc"):
        if v in ds:
            data[v] = xr.DataArray(ds[v].values, dims=("yc", "xc"), attrs=ds[v].attrs)
    data["convc"] = xr.DataArray(convc.astype(np.float32), dims=("yc", "xc"),
                                 attrs=dict(units="degrees", source=orient,
                                            long_name="compass bearing of grid north"))
    data["bathymetry"] = xr.DataArray(
        np.where(wet, bathy, H_LAND).astype(np.float32), dims=("yc", "xc"),
        attrs=dict(units="m", long_name="bathymetry used (topo + adjust)"))

    coords = {c: ds[c].values for c in ("xc", "yc") if c in ds}
    outds = xr.Dataset(data, coords=coords)
    outds.attrs = dict(
        title="Effective fetch for the GETM-BFM Silt wave scheme",
        source=f"wave_effective_fetch.py, {time.strftime('%Y-%m-%d %H:%M')}",
        topo_file=os.path.abspath(topo),
        bathymetry_adjust=os.path.abspath(adjust) if adjust else "",
        bearings="geographic, direction the wind blows from, 0..350 step 10 deg",
        sector=f"+-{half_sector:g} deg, {n_sub} cosine-weighted sub-rays",
        blocking="depth < min(h_block, h_0 - delta)", delta_m=delta,
        max_fetch_m=max_fetch, open_edges=open_edges, grid_orientation=orient,
        land_cells=("missing value -1" if land == "missing" else "nearest wet value"),
        wave_method_2=f"fetch_dir (h_block {h_dir}), fetch_exp, fetch_tp (h_block {h_tp})")

    enc = {}
    for v in outds.data_vars:
        fetch = v.startswith("fetch_") and land == "missing"
        enc[v] = {"zlib": True, "complevel": 4,
                  "_FillValue": np.float32(LAND_VALUE) if fetch else None}
        if fetch:
            outds[v].attrs["missing_value"] = np.float32(LAND_VALUE)
    for c in coords:
        enc[c] = {"_FillValue": None}
    if os.path.exists(out):
        os.remove(out)
    outds.to_netcdf(out, encoding=enc, format="NETCDF4_CLASSIC")

    fe = outds.fetch_exp.values[wet]
    print(f"fetch_exp range {np.nanmin(fe) / 1e3:.2f} to {np.nanmax(fe) / 1e3:.2f} km")
    print("wrote", out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("topo", help="GETM bathymetry file (topo.nc)")
    ap.add_argument("-a", "--adjust", default=None,
                    help="GETM bathymetry.adjust file (default: none)")
    ap.add_argument("-o", "--out", default="effective_fetch.nc", help="output NetCDF file")
    ap.add_argument("--h-dir", type=float, default=DEFAULTS["h_dir"],
                    help="blocking depth (m) for fetch_dir (default %(default)s)")
    ap.add_argument("--h-tp", type=float, default=DEFAULTS["h_tp"],
                    help="blocking depth (m) for fetch_tp (default %(default)s)")
    ap.add_argument("--delta", type=float, default=DEFAULTS["delta"],
                    help="depth margin below the origin depth (m) (default %(default)s)")
    ap.add_argument("--max-fetch", type=float, default=DEFAULTS["max_fetch"],
                    help="fetch of rays reaching open sea (m) (default %(default)g)")
    ap.add_argument("--half-sector", type=float, default=DEFAULTS["half_sector"],
                    help="half-width of the averaging sector (deg) (default %(default)s)")
    ap.add_argument("--n-sub", type=int, default=DEFAULTS["n_sub"],
                    help="sub-rays per sector (default %(default)s)")
    ap.add_argument("--open-edges", default=DEFAULTS["open_edges"],
                    help="grid edges open to the sea, any of W E S N (default %(default)s)")
    ap.add_argument("--land", choices=["missing", "nearest"], default="missing",
                    help="land cells: missing value -1 (default) or nearest wet value")
    ap.add_argument("--grid-north", type=float, default=None,
                    help="compass bearing of grid north (deg) if the topo file has no "
                         "convc (default 0, as GETM)")
    ap.add_argument("-q", "--quiet", action="store_true", help="no progress per bearing")
    a = ap.parse_args()
    build(a.topo, a.out, a.adjust, a.h_dir, a.h_tp, a.delta, a.max_fetch,
          a.half_sector, a.n_sub, a.open_edges, a.land, a.grid_north, not a.quiet)


if __name__ == "__main__":
    main()
