"""House figure style for the Wad_EMOaaS validation notebooks.

Nature figure guide + SciencePlots ("science", "nature", "no-latex") on a white
background, Okabe-Ito categorical colours with fixed entity assignments,
cmcrameri / cmocean continuous maps, GSHHG full-resolution land for maps, and an
atomic writer that produces a vector PDF, a 600 dpi PNG and a CSV twin of the
plotted numbers for every figure.

Import it from a notebook in this folder:

    import figstyle as fs
    fs.use_style()
    fig, ax = fs.figure("single", 60)
    ...
    fs.save_figure(fig, "fig01_topic", OUT_DIR, data=df)
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

# ── sizes ─────────────────────────────────────────────────────────────────────
MM = 1 / 25.4
WIDTH_MM = {"single": 89, "onehalf": 120, "double": 183}
MAX_HEIGHT_MM = 247

# ── ink and map colours ──────────────────────────────────────────────────────
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#898781"
HAIRLINE = "#e1e0d9"
LAND, COAST = "#e2ded4", "#8f8c84"

OKABE_ITO = {
    "blue": "#0072B2", "orange": "#E69F00", "green": "#009E73",
    "vermillion": "#D55E00", "purple": "#CC79A7", "sky": "#56B4E9",
    "yellow": "#F0E442",
}
CATEGORICAL = [OKABE_ITO[k] for k in
               ("blue", "orange", "green", "vermillion", "purple", "sky")]

# Fixed entity colours: the same run / source keeps its colour in every figure.
RUN_COLOURS = {"spinup_01": OKABE_ITO["orange"], "spinup_02": OKABE_ITO["blue"],
               "spinup_10": OKABE_ITO["vermillion"]}
SOURCE_COLOURS = {"SIBES": OKABE_ITO["green"], "SUBES": OKABE_ITO["purple"]}
SOURCE_MARKERS = {"SIBES": "o", "SUBES": "s", "NIOZ Jetty": "o", "RWS": "s"}
OBS_COLOUR = INK

# Benthic feeding groups: the first four colours of cmcrameri batlowS, in fixed
# order. They differ in lightness as well as hue, so stacked bars stay readable.
GROUP_COLOURS = {"Y1c": "#011959", "Y2c": "#faccfa", "Y3c": "#828231", "Y5c": "#215f60"}


def run_colours(names) -> dict:
    """Colour per model run: fixed ones first, others take unused colours in order.

    Colours reserved for other known runs or for observation sources are never
    handed out, so a new run cannot be confused with an existing one.
    """
    out = {n: RUN_COLOURS[n] for n in names if n in RUN_COLOURS}
    spare = [c for c in CATEGORICAL if c not in out.values()
             and c not in RUN_COLOURS.values() and c not in SOURCE_COLOURS.values()]
    for n in names:
        if n not in out:
            out[n] = spare.pop(0) if spare else INK3
    return out


# ── rcParams ─────────────────────────────────────────────────────────────────
def use_style() -> None:
    """SciencePlots science+nature+no-latex, then the house overrides."""
    try:
        import scienceplots  # noqa: F401  (registers the styles)
        plt.style.use(["science", "nature", "no-latex"])
    except Exception:
        plt.style.use("default")
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "mathtext.fontset": "custom",
        "mathtext.rm": "sans", "mathtext.it": "sans:italic", "mathtext.bf": "sans:bold",
        "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7,
        "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
        "legend.title_fontsize": 6.5,
        "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": INK,
        "xtick.color": INK, "ytick.color": INK,
        "axes.linewidth": 0.5, "lines.linewidth": 1.1, "patch.linewidth": 0.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "grid.color": HAIRLINE, "grid.linewidth": 0.3,
        "axes.prop_cycle": mpl.cycler(color=CATEGORICAL),
        "axes.titlepad": 3, "axes.labelpad": 2,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.top": False, "ytick.right": False,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
        "xtick.major.width": 0.5, "ytick.major.width": 0.5,
        "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
        "xtick.major.pad": 2, "ytick.major.pad": 2,
        "xtick.minor.visible": True, "ytick.minor.visible": True,
        "legend.frameon": False, "legend.handlelength": 1.6,
        "legend.borderaxespad": 0.3, "legend.handletextpad": 0.5,
        "legend.columnspacing": 1.2, "legend.labelspacing": 0.3,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "savefig.edgecolor": "white",
        "savefig.dpi": 600, "savefig.bbox": None, "savefig.pad_inches": 0.02,
        "figure.dpi": 150,
        "figure.constrained_layout.use": True,
        "figure.constrained_layout.h_pad": 2 / 72, "figure.constrained_layout.w_pad": 2 / 72,
        "figure.constrained_layout.hspace": 0.02, "figure.constrained_layout.wspace": 0.02,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "image.cmap": "cmc.batlow" if "cmc.batlow" in mpl.colormaps else "viridis",
    })


def figure(width="double", height_mm=80, nrows=1, ncols=1, **kw):
    """Figure at a journal width ('single', 'onehalf', 'double' or mm)."""
    w = WIDTH_MM.get(width, width) if isinstance(width, str) else width
    h = min(height_mm, MAX_HEIGHT_MM)
    fig, axes = plt.subplots(nrows, ncols, figsize=(w * MM, h * MM), **kw)
    return fig, axes


def open_frame(ax) -> None:
    """Full frame (maps, sections, Taylor-like panels)."""
    for s in ax.spines.values():
        s.set_visible(True)


# ── colour maps ──────────────────────────────────────────────────────────────
def _truncate(cmap, lo, hi, name):
    return mcolors.LinearSegmentedColormap.from_list(name, cmap(np.linspace(lo, hi, 256)))


def cmap_diverging():
    """cmcrameri vik: blue = model too low, red = model too high."""
    from cmcrameri import cm
    return cm.vik


def cmap_density():
    """Light-to-dark single hue for point densities (cmcrameri lapaz, reversed)."""
    from cmcrameri import cm
    return _truncate(cm.lapaz_r, 0.10, 1.0, "lapaz_density")


def cmap_bathy_light():
    """Light, recessive bathymetry ramp for map backgrounds (cmocean deep, faded)."""
    import cmocean
    base = cmocean.cm.deep(np.linspace(0.02, 0.60, 256))
    base[:, :3] = 0.55 * base[:, :3] + 0.45          # fade towards white
    return mcolors.ListedColormap(base, name="deep_light")


def nice_limit(values, q=98.0, floor=None) -> float:
    """Symmetric limit: q-th percentile of |values| rounded up to 1-2-2.5-5 x 10^k."""
    v = np.abs(np.asarray(values, float))
    v = v[np.isfinite(v)]
    if v.size == 0:
        return 1.0
    x = float(np.percentile(v, q))
    if floor is not None:
        x = max(x, floor)
    if x <= 0:
        return 1.0
    k = np.floor(np.log10(x))
    for m in (1, 2, 2.5, 5, 10):
        if m * 10 ** k >= x:
            return float(m * 10 ** k)
    return float(10 ** (k + 1))


def diverging_colorbar(fig, mappable, *, ax=None, cax=None, label="",
                       low_text="model < obs", high_text="model > obs",
                       orientation="vertical", ticks=None, ticklabels=None,
                       extend="neither", **kw):
    """Colourbar for a zero-centred quantity, with labelled ends."""
    cb = fig.colorbar(mappable, ax=ax, cax=cax, orientation=orientation,
                      extend=extend, **kw)
    cb.outline.set_linewidth(0.4)
    cb.ax.tick_params(which="both", length=2, width=0.4)
    cb.ax.minorticks_off()
    if ticks is not None:
        cb.set_ticks(ticks)
        if ticklabels is not None:
            cb.set_ticklabels(ticklabels)
    cb.set_label(label)
    small = dict(fontsize=6, color=INK2, style="italic", transform=cb.ax.transAxes)
    # the extend triangles are drawn outside cb.ax, so clear them
    ext = kw.get("extendfrac", 0.05)
    ext = ext if isinstance(ext, (int, float)) else 0.05
    lo_pad = (ext if extend in ("both", "min") else 0.0) + 0.015
    hi_pad = (ext if extend in ("both", "max") else 0.0) + 0.015
    if orientation == "vertical":
        cb.ax.text(0.5, 1.0 + hi_pad, high_text, ha="center", va="bottom", **small)
        cb.ax.text(0.5, -lo_pad, low_text, ha="center", va="top", **small)
    else:
        cb.ax.text(-lo_pad, 0.5, low_text, ha="right", va="center", **small)
        cb.ax.text(1.0 + hi_pad, 0.5, high_text, ha="left", va="center", **small)
    return cb


def halo(width=1.6, colour="white"):
    """Path effect that keeps text legible over map features."""
    import matplotlib.patheffects as pe
    return [pe.withStroke(linewidth=width, foreground=colour)]


# ── annotations ──────────────────────────────────────────────────────────────
def panel_label(ax, letter, dx_pt=None, dy_pt=3.0) -> None:
    """Bold lowercase panel letter just outside the top-left corner of *ax*.

    The horizontal offset defaults to the width of the y-tick labels and
    y-label, so the letter sits flush with the left edge of the panel
    including its annotations.
    """
    fig = ax.figure
    if dx_pt is None:
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        tight = ax.get_tightbbox(r)
        box = ax.get_window_extent(r)
        dx_pt = -(box.x0 - tight.x0) * 72 / fig.dpi if tight is not None else -8
    t = ax.annotate(letter, xy=(0, 1), xycoords="axes fraction",
                    xytext=(dx_pt, dy_pt), textcoords="offset points",
                    ha="left", va="bottom", fontsize=8, fontweight="bold",
                    color=INK, annotation_clip=False)
    t.set_in_layout(True)


def corner_note(ax, text, x=None, y=None, corners=("upper left", "lower right",
                                                   "upper right", "lower left"),
                box=(0.42, 0.30), pad=0.03, **kw):
    """Put a short note in whichever corner holds the fewest data points.

    *x*, *y* are the plotted data (in data units). Call after limits and scales
    are final.
    """
    best = corners[0]
    if x is not None and len(x):
        xy = np.column_stack([np.asarray(x, float), np.asarray(y, float)])
        xy = xy[np.all(np.isfinite(xy), axis=1)]
        f = ax.transAxes.inverted().transform(ax.transData.transform(xy))
        bw, bh = box
        counts = {}
        for c in corners:
            xin = f[:, 0] < bw if "left" in c else f[:, 0] > 1 - bw
            yin = f[:, 1] > 1 - bh if "upper" in c else f[:, 1] < bh
            counts[c] = int((xin & yin).sum())
        best = min(corners, key=lambda c: (counts[c], corners.index(c)))
    xa = pad if "left" in best else 1 - pad
    ya = 1 - pad if "upper" in best else pad
    opts = dict(fontsize=6.5, color=INK, linespacing=1.25, zorder=10)
    opts.update(kw)
    return ax.text(xa, ya, text, transform=ax.transAxes,
                   ha="left" if "left" in best else "right",
                   va="top" if "upper" in best else "bottom", **opts)


def _no_negative_zero(s: str) -> str:
    try:
        if s.startswith("-") and float(s) == 0:
            return s[1:]
    except ValueError:
        pass
    return s


def signed(v, fmt=".2f") -> str:
    """Number with an explicit sign and a true minus (U+2212); never '-0.00'."""
    s = format(v, "+" + fmt)
    if s.startswith("-") and float(s) == 0:
        s = "+" + s[1:]
    return s.replace("-", "−")


def unsigned(v, fmt=".2f") -> str:
    """Number with a true minus (U+2212); never '-0.00'."""
    return _no_negative_zero(format(v, fmt)).replace("-", "−")


def stats_line(ax, text, fontsize=6, color=None, pad=2.0, ha="center", **kw):
    """Skill scores just above the panel (left, centre or right), never on the data."""
    x = {"left": 0.0, "center": 0.5, "right": 1.0}[ha]
    return ax.annotate(text, xy=(x, 1.0), xycoords="axes fraction",
                       xytext=(0, pad), textcoords="offset points", ha=ha,
                       va="bottom", fontsize=fontsize, color=color or INK2, **kw)


def _overlap(a, b) -> float:
    w = min(a.x1, b.x1) - max(a.x0, b.x0)
    h = min(a.y1, b.y1) - max(a.y0, b.y0)
    return w * h if (w > 0 and h > 0) else 0.0


def place_labels(ax, x, y, texts, *, avoid_x=None, avoid_y=None, fontsize=6.5,
                 color=INK, radii=(3.5, 7, 11, 16), leader_from=10, order=None,
                 stay_inside=True, point_pad_pt=2.5, **kw):
    """Greedy, collision-aware text labels next to points.

    Tries eight directions at increasing distance and keeps the cheapest
    spot: overlapping an earlier label costs most, covering a marker (points
    are treated as boxes of +-point_pad_pt) next, leaving the axes is heavily
    penalised, and distance a little. Labels pushed further than
    *leader_from* points get a hairline leader. Call it LAST, after colourbars
    and legends exist, so that the layout no longer changes.
    """
    fig = ax.figure
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    axbb = ax.get_window_extent(r)
    ppad = point_pad_pt * fig.dpi / 72
    x = np.asarray(x, float); y = np.asarray(y, float)
    pts = ax.transData.transform(np.column_stack([x, y]))
    avoid = pts
    if avoid_x is not None:
        extra = ax.transData.transform(np.column_stack([avoid_x, avoid_y]))
        avoid = np.vstack([pts, extra])
    dirs = [(1, 0, "left", "center"), (-1, 0, "right", "center"),
            (0, 1, "center", "bottom"), (0, -1, "center", "top"),
            (0.75, 0.75, "left", "bottom"), (-0.75, 0.75, "right", "bottom"),
            (0.75, -0.75, "left", "top"), (-0.75, -0.75, "right", "top")]
    placed, out = [], []
    idx = range(len(texts)) if order is None else order
    for i in idx:
        best = None
        for rad in radii:
            for dx, dy, ha, va in dirs:
                t = ax.annotate(texts[i], (x[i], y[i]), xytext=(dx * rad, dy * rad),
                                textcoords="offset points", ha=ha, va=va,
                                fontsize=fontsize, color=color, **kw)
                bb = t.get_window_extent(r).expanded(1.04, 1.10)
                t.remove()
                area = max(bb.width * bb.height, 1.0)
                cost = sum(_overlap(bb, p) for p in placed) / area * 300
                inside = ((avoid[:, 0] > bb.x0 - ppad) & (avoid[:, 0] < bb.x1 + ppad)
                          & (avoid[:, 1] > bb.y0 - ppad) & (avoid[:, 1] < bb.y1 + ppad))
                cost += 40 * int(inside.sum())
                if stay_inside and not (bb.x0 >= axbb.x0 and bb.x1 <= axbb.x1
                                        and bb.y0 >= axbb.y0 and bb.y1 <= axbb.y1):
                    cost += 600
                cost += 0.3 * rad
                if best is None or cost < best[0]:
                    best = (cost, (dx * rad, dy * rad), ha, va, bb, rad)
            if best[0] <= 0.3 * rad + 1e-9:
                break
        _, off, ha, va, bb, rad = best
        arrow = (dict(arrowstyle="-", lw=0.3, color=INK3, shrinkA=0, shrinkB=1.5)
                 if rad >= leader_from else None)
        opts = {"zorder": 11}          # above land (4) and markers (8)
        opts.update(kw)
        t = ax.annotate(texts[i], (x[i], y[i]), xytext=off, textcoords="offset points",
                        ha=ha, va=va, fontsize=fontsize, color=color,
                        arrowprops=arrow, **opts)
        t.set_in_layout(False)
        placed.append(bb)
        out.append(t)
    return out


def repel_points(ax, x, y, min_sep_pt=4.0, iters=300):
    """Nudge overlapping markers apart (display space); returns new x, y.

    Use for co-located stations so that no marker hides another. Draw a
    hairline from the true to the displayed position where they differ.
    """
    fig = ax.figure
    fig.canvas.draw()
    P = ax.transData.transform(np.column_stack([x, y]))
    Q = P.copy()
    d_min = min_sep_pt * fig.dpi / 72
    rng = np.random.default_rng(0)
    for _ in range(iters):
        moved = False
        for i in range(len(Q)):
            for j in range(i + 1, len(Q)):
                d = Q[j] - Q[i]
                dist = float(np.hypot(*d))
                if dist < d_min:
                    if dist < 1e-6:
                        d = rng.normal(size=2); dist = float(np.hypot(*d))
                    push = (d_min - dist) / 2 * d / dist
                    Q[i] -= push; Q[j] += push
                    moved = True
        if not moved:
            break
    new = ax.transData.inverted().transform(Q)
    return new[:, 0], new[:, 1]


# ── output ───────────────────────────────────────────────────────────────────
def _atomic(path: Path, writer) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}.", suffix=path.suffix)
    os.close(fd)
    try:
        writer(tmp)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def save_figure(fig, name, outdir, data=None, dpi=600, close=False) -> None:
    """Write <name>.pdf (vector, editable text) + <name>.png (600 dpi) + <name>.csv.

    *data* is a DataFrame, or a dict of DataFrames that is stacked into one
    long table with a 'panel' column. Every file is written atomically.
    """
    outdir = Path(outdir)
    paths = []
    for ext in ("pdf", "png"):
        p = outdir / f"{name}.{ext}"
        _atomic(p, lambda tmp, ext=ext: fig.savefig(tmp, format=ext, dpi=dpi))
        paths.append(p)
    if data is not None:
        if isinstance(data, dict):
            data = pd.concat({k: pd.DataFrame(v) for k, v in data.items()},
                             names=["panel"]).reset_index(level=0)
        p = outdir / f"{name}.csv"
        _atomic(p, lambda tmp: data.to_csv(tmp, index=not isinstance(data.index, pd.RangeIndex)))
        paths.append(p)
    print(f"  -> {name}  ({', '.join(q.suffix[1:] for q in paths)})")
    if close:
        plt.close(fig)


# ── GETM grid helpers ────────────────────────────────────────────────────────
def fill_coord(a, name="", verbose=True):
    """Fill missing (-999 / NaN) GETM lon or lat values.

    A GETM grid is close to linear in index space, so interior holes are
    interpolated and anything outside the convex hull (halo ring) is
    extrapolated from a least-squares plane.
    """
    a = np.asarray(np.ma.filled(a, np.nan), dtype=float)
    a = np.where(np.abs(a) > 360, np.nan, a)
    bad = ~np.isfinite(a)
    if not bad.any():
        return a
    jj, ii = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    good = ~bad
    A = np.column_stack([np.ones(good.sum()), ii[good], jj[good]])
    coef, *_ = np.linalg.lstsq(A, a[good], rcond=None)
    plane = coef[0] + coef[1] * ii + coef[2] * jj
    resid = float(np.abs(a[good] - plane[good]).max())
    # smooth trend (quadratic in index space) + interpolated residual: continuous
    # across the edge of the valid region, so pcolormesh cell edges stay monotonic
    def design(i, j):
        return np.column_stack([np.ones_like(i), i, j, i * j, i ** 2, j ** 2]).astype(float)
    cq, *_ = np.linalg.lstsq(design(ii[good], jj[good]), a[good], rcond=None)
    trend = (design(ii.ravel(), jj.ravel()) @ cq).reshape(a.shape)
    res = np.where(good, a - trend, np.nan)
    try:
        from scipy.interpolate import griddata
        pts = (ii[good], jj[good])
        fill = griddata(pts, res[good], (ii[bad], jj[bad]), method="linear")
        miss = ~np.isfinite(fill)
        if miss.any():
            fill[miss] = griddata(pts, res[good], (ii[bad][miss], jj[bad][miss]),
                                  method="nearest")
        res[bad] = fill
    except Exception:
        res[bad] = 0.0
    out = np.where(good, a, trend + res)
    if verbose:
        print(f"  {name}: filled {int(bad.sum())} of {a.size} ({100 * bad.mean():.1f}%), "
              f"plane residual {resid:.4f} deg")
    return out


def grid_outline(lon2d, lat2d, valid=None):
    """Perimeter of a GETM grid as two 1-D arrays.

    Edge cells are often halo / fill values, so lon and lat are fitted with a
    quadratic in index space on the *valid* cells and evaluated along the
    index perimeter. That traces the computational domain without the kinks
    that extrapolated halo cells produce.
    """
    lon2d = np.asarray(lon2d, float); lat2d = np.asarray(lat2d, float)
    if valid is None:
        valid = np.isfinite(lon2d) & np.isfinite(lat2d) & (np.abs(lon2d) <= 360)
    jj, ii = np.mgrid[0:lon2d.shape[0], 0:lon2d.shape[1]]

    def design(i, j):
        i = np.asarray(i, float); j = np.asarray(j, float)
        return np.column_stack([np.ones_like(i), i, j, i * j, i ** 2, j ** 2])

    A = design(ii[valid], jj[valid])
    c_lon, *_ = np.linalg.lstsq(A, lon2d[valid], rcond=None)
    c_lat, *_ = np.linalg.lstsq(A, lat2d[valid], rcond=None)
    ny, nx = lon2d.shape
    i_p = np.concatenate([np.arange(nx), np.full(ny, nx - 1), np.arange(nx)[::-1], np.zeros(ny)])
    j_p = np.concatenate([np.zeros(nx), np.arange(ny), np.full(nx, ny - 1), np.arange(ny)[::-1]])
    B = design(i_p, j_p)
    return B @ c_lon, B @ c_lat


# ── maps ─────────────────────────────────────────────────────────────────────
GSHHG_MIRROR = "https://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-2.3.7.zip"


def _gshhg_path(scale, level):
    """Local path of a GSHHG shapefile, downloading it if needed.

    cartopy's own downloader points at an NOAA URL that no longer resolves, so
    fall back to the SOEST mirror and unpack into cartopy's data directory,
    where cartopy will find it next time.
    """
    import cartopy
    import cartopy.io.shapereader as shpreader
    target = (Path(cartopy.config["data_dir"]) / "shapefiles" / "gshhs" / scale
              / f"GSHHS_{scale}_L{level}.shp")
    if target.exists():
        return str(target)
    try:
        return str(shpreader.gshhs(scale, level))
    except Exception:
        pass
    import io
    import urllib.request
    import zipfile
    print(f"downloading GSHHG shapefiles from {GSHHG_MIRROR} (one-off, ~150 MB)")
    with urllib.request.urlopen(GSHHG_MIRROR, timeout=600) as fh:
        zf = zipfile.ZipFile(io.BytesIO(fh.read()))
    for member in zf.namelist():
        parts = Path(member).parts
        if (len(parts) == 3 and parts[0] == "GSHHS_shp" and parts[1] == scale
                and not member.endswith("/")):
            dest = target.parent.parent / parts[1] / parts[2]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(member))
    return str(target)


def load_land(extent, cache_dir=None, scale="f"):
    """GSHHG land (level 1 minus level-2 lakes) clipped to *extent*.

    extent = (lon_min, lon_max, lat_min, lat_max). The global shapefile is
    downloaded once by cartopy; the clipped geometry is cached as WKB so later
    calls are instant.
    """
    from shapely import wkb
    from shapely.geometry import box
    from shapely.ops import unary_union

    pad = 0.3
    bb = (extent[0] - pad, extent[2] - pad, extent[1] + pad, extent[3] + pad)
    cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "wad_emoaas"
    key = "gshhg_{}_{:.2f}_{:.2f}_{:.2f}_{:.2f}.wkb".format(scale, *bb)
    cache = cache_dir / key
    if cache.exists():
        return wkb.loads(cache.read_bytes())

    import cartopy.io.shapereader as shpreader
    clip = box(*bb)

    def level(n):
        path = _gshhg_path(scale, n)
        try:
            geoms = shpreader.Reader(path, bbox=bb).geometries()
        except TypeError:
            geoms = shpreader.Reader(path).geometries()
        parts = [g.intersection(clip) for g in geoms if g.intersects(clip)]
        return unary_union(parts) if parts else None

    land = level(1)
    lakes = level(2)
    if land is not None and lakes is not None:
        land = land.difference(lakes)
    cache_dir.mkdir(parents=True, exist_ok=True)
    _atomic(cache, lambda tmp: Path(tmp).write_bytes(wkb.dumps(land)))
    return land


def _geom_to_path(geom):
    from shapely.geometry.polygon import orient
    polys = []
    stack = [geom]
    while stack:
        g = stack.pop()
        if g is None or g.is_empty:
            continue
        if g.geom_type == "Polygon":
            polys.append(g)
        elif hasattr(g, "geoms"):
            stack.extend(g.geoms)
    verts, codes = [], []
    for p in polys:
        p = orient(p, 1.0)
        for ring in [p.exterior, *p.interiors]:
            xy = np.asarray(ring.coords)
            if len(xy) < 3:
                continue
            verts.append(xy)
            codes.append([MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY])
    return MPath(np.concatenate(verts), np.concatenate(codes))


def add_land(ax, land, zorder=4):
    """Land fill #e2ded4 with a hairline coast #8f8c84."""
    if land is None or land.is_empty:
        return None
    patch = PathPatch(_geom_to_path(land), facecolor=LAND, edgecolor=COAST,
                      linewidth=0.3, zorder=zorder)
    ax.add_patch(patch)
    return patch


def _deg_formatter(hemi_pos, hemi_neg):
    def fmt(v, _):
        s = f"{abs(v):.10g}"
        return f"{s}°{hemi_pos if v >= 0 else hemi_neg}"
    return mticker.FuncFormatter(fmt)


def setup_map(ax, extent, lat0=None, xstep=0.5, ystep=0.2, labels=(True, True)):
    """Equirectangular map axes: aspect 1/cos(lat), full frame, degree ticks."""
    lat0 = lat0 if lat0 is not None else 0.5 * (extent[2] + extent[3])
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect(1 / np.cos(np.radians(lat0)))
    open_frame(ax)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(xstep))
    ax.yaxis.set_major_locator(mticker.MultipleLocator(ystep))
    ax.xaxis.set_minor_locator(mticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(mticker.AutoMinorLocator(2))
    ax.xaxis.set_major_formatter(_deg_formatter("E", "W"))
    ax.yaxis.set_major_formatter(_deg_formatter("N", "S"))
    ax.tick_params(labelbottom=labels[0], labelleft=labels[1])
    ax.set_facecolor("white")
    return ax


def add_scalebar(ax, length_km, loc="lower left", pad=0.04, lat0=None, zorder=8):
    """Plain ink scale bar with end ticks, sized for latitude *lat0*."""
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    lat0 = lat0 if lat0 is not None else 0.5 * (y0 + y1)
    dlon = length_km / (111.32 * np.cos(np.radians(lat0)))
    xs = x0 + pad * (x1 - x0) if "left" in loc else x1 - pad * (x1 - x0) - dlon
    ys = y0 + pad * (y1 - y0) * 1.2 if "lower" in loc else y1 - pad * (y1 - y0) * 2.2
    tick = 0.012 * (y1 - y0)
    kw = dict(color=INK, lw=0.8, solid_capstyle="butt", zorder=zorder)
    ax.plot([xs, xs + dlon], [ys, ys], **kw)
    ax.plot([xs, xs], [ys - tick, ys + tick], **kw)
    ax.plot([xs + dlon, xs + dlon], [ys - tick, ys + tick], **kw)
    ax.annotate(f"{length_km:g} km", (xs + dlon / 2, ys), xytext=(0, 2),
                textcoords="offset points", ha="center", va="bottom",
                fontsize=6.5, color=INK, zorder=zorder, path_effects=halo())


def add_water_label(ax, lon, lat, text, **kw):
    opts = dict(fontsize=6.5, color=INK2, style="italic", ha="center", va="center",
                zorder=7)
    opts.update(kw)
    return ax.text(lon, lat, text, **opts)


def add_bathymetry(ax, lon2d, lat2d, depth, vmin=-2.0, vmax=30.0, zorder=1):
    """Recessive water shading from model depth (positive down), rasterised."""
    pm = ax.pcolormesh(lon2d, lat2d, np.ma.masked_invalid(depth),
                       cmap=cmap_bathy_light(), vmin=vmin, vmax=vmax,
                       shading="auto", rasterized=True, zorder=zorder)
    return pm


def add_domain_outline(ax, lon2d, lat2d, colour, valid=None, lw=0.7, zorder=6,
                       label=None):
    """Computational-domain outline in the model colour (see grid_outline)."""
    lo, la = grid_outline(lon2d, lat2d, valid)
    return ax.plot(lo, la, color=colour, lw=lw, zorder=zorder, label=label)[0]
