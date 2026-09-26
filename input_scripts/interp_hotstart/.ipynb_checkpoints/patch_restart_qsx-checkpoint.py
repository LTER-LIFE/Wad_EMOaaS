"""Prepare a COPY of a GETM/BFM NetCDF hotstart file for the first run with Silt.nml
silt_bottom=2 (sediment fix F2): write the buffer-layer silt QSx (mg/m2) from the SIBES/SUBES mud
map and empty the fluff layer DSm.

Why:
- QSx. With hotstart_bio=.true. the benthic states come from the restart. A restart from the
  compiled model (silt_bottom=1, sw_BenSilt=0) holds QSx = 0, so Silt.F90 would fill the buffer
  on the first call from psilt * 1600 kg/m3 * 0.1 m instead of the mud map F2 was calibrated with
  (sediment_fixes/SEDIMENT_FIXES.md, sediment_year/YEAR_TEST.md).
- DSm. silt_bottom=2 uses DSm as the fluff thickness (fluff = DSm * bed_rho_fluff). Restarts can
  hold DSm of about 0.5 m from the benthic initial file (unused while sw_BenSilt=0), which would
  start the run with about 250 kg/m2 of fluff. DSm is set to 0 (empty fluff) in the patched cells;
  nothing else uses DSm while sw_BenSilt=0.

Grid: the map is on the topo grid (xc, yc); the restart can be larger (padded to the parallel
decomposition, e.g. 336 x 195 against 328 x 194). Cells are matched by coordinate
(xax/yax against xc/yc). Only cells where the restart holds a value (not _FillValue) and the map is
finite are changed. The file is modified in place with netCDF4 (never rewritten), so the variable
order that read_restart_bio_ncdf.F90 relies on is unchanged.

    python patch_restart_qsx.py restart_in restart_out [buffer_init_QSx.nc] [--keep-dsm]

Then point link_restartfiles (restart_file=) to restart_out. Needs numpy and netCDF4.
"""
import os
import shutil
import sys

import numpy as np
from netCDF4 import Dataset

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MAP = os.path.join(HERE, "..", "..", "sediment_fixes", "results", "buffer_init_QSx.nc")


def fill_value(v):
    for a in ("_FillValue", "missing_value"):
        if a in v.ncattrs():
            return float(v.getncattr(a))
    return None


def is_fill(a, fv):
    bad = ~np.isfinite(a)
    if fv is not None:
        bad |= np.isclose(a, fv)
    return bad


def match(coord_restart, coord_map, name):
    """Index of each map coordinate in the restart coordinate (exact to 1 m)."""
    idx = np.searchsorted(coord_restart, coord_map)
    idx = np.clip(idx, 0, len(coord_restart) - 1)
    if not np.allclose(coord_restart[idx], coord_map, atol=1.0):
        sys.exit(f"{name}: map coordinates not found in the restart; not patched")
    return idx


def main(src, dst, mapfile=DEFAULT_MAP, keep_dsm=False):
    if os.path.abspath(src) == os.path.abspath(dst):
        sys.exit("refusing to overwrite the input restart; give a new output name")
    if os.path.exists(dst):
        sys.exit(f"{dst} exists; remove it first")
    with Dataset(mapfile) as m:
        m.set_auto_mask(False)
        q = np.array(m["QSx"][:], dtype="f8")
        q[is_fill(q, fill_value(m["QSx"]))] = np.nan
        xc, yc = np.array(m["xc"][:], "f8"), np.array(m["yc"][:], "f8")

    with Dataset(src) as nc:                      # check everything before copying
        for n in ("QSx", "xax", "yax"):
            if n not in nc.variables:
                sys.exit(f"no variable {n} in the restart (is this a bio hotstart file?)")
        v = nc["QSx"]
        if v.dimensions[-2:] != ("yax", "xax"):
            sys.exit(f"QSx dims {v.dimensions}, expected (..., yax, xax); not patched")
        ix = match(np.array(nc["xax"][:], "f8"), xc, "x")
        iy = match(np.array(nc["yax"][:], "f8"), yc, "y")
        print(f"QSx in restart: shape {v.shape}; map {q.shape} at restart rows "
              f"{iy[0]}-{iy[-1]}, columns {ix[0]}-{ix[-1]}")

    shutil.copy2(src, dst)
    with Dataset(dst, "r+") as nc:
        nc.set_auto_mask(False)
        v = nc["QSx"]
        old = np.array(v[:], dtype="f8")
        qm = np.full(old.shape[-2:], np.nan)
        qm[np.ix_(iy, ix)] = q
        valid = ~is_fill(old, fill_value(v))
        if valid.ndim > 2:
            valid = valid.all(axis=tuple(range(valid.ndim - 2)))
        ok = valid & np.isfinite(qm)
        # restart cells with a value but no map value: land in the model (QSx = 0 there) or
        # wet cells outside the map; the latter keep QSx (Silt then initialises from psilt)
        print(f"  restart cells with values: {valid.sum()}; patched (map available): {ok.sum()}")
        print(f"  map cells without restart value (land/boundary in the model, left as is): "
              f"{(np.isfinite(qm) & ~valid).sum()}")
        new = old.copy()
        new[..., ok] = qm[ok]
        v[:] = new
        for name, a in (("old", old[..., ok]), ("new", new[..., ok])):
            p = np.percentile(a, [1, 50, 99])
            print(f"  {name} QSx (kg/m2): p1 {p[0]/1e6:.3g}  median {p[1]/1e6:.3g}  p99 {p[2]/1e6:.3g}")

        if "DSm" in nc.variables:
            dv = nc["DSm"]
            d = np.array(dv[:], dtype="f8")
            p = np.percentile(d[..., ok], [0, 50, 100])
            print(f"  DSm in patched cells: min {p[0]:.3g}  median {p[1]:.3g}  max {p[2]:.3g} m")
            if keep_dsm:
                print("  DSm kept (--keep-dsm): initial fluff = DSm * bed_rho_fluff")
            else:
                d[..., ok] = 0.0
                dv[:] = d
                print("  DSm set to 0 in the patched cells (empty fluff layer)")
    print("wrote", dst)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--keep-dsm"]
    if len(args) not in (2, 3):
        sys.exit(__doc__)
    main(*args, keep_dsm="--keep-dsm" in sys.argv[1:])
