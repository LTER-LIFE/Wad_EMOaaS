import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

from scipy.interpolate import RegularGridInterpolator
from matplotlib.animation import FuncAnimation
from pathlib import Path
from IPython.display import HTML

# meta data:
#! BFM biological model

# pelagic variables (group PelVariables):
#! pelagic  (O)              O2:   Oxygen (mmol/m3)
#! pelagic  (P)              N1:   Phosphate (mmol/m3)
#! pelagic  (N)              N3:   Nitrate (mmol/m3)
#! pelagic  (N)              N4:   Ammonium (mmol/m3)
#! pelagic  (Si)             N5:   Silicate (mmol/m3)
#! pelagic  (R)              N6:   Reduction Equivalents (mmol/m3)
#! pelagic  (N)              O4:   N2-sink (mmol/m3)
#! pelagic  (CNP)            B1:   Pelagic Bacteria
#! pelagic  (CNPSiI)         P1:   Diatoms (group PhytoPlankton))
#! pelagic  (CNPSiI)         P2:   Flagellates (group PhytoPlankton))
#! pelagic  (CNPSiI)         P3:   PicoPhytoPlankton (group PhytoPlankton))
#! pelagic  (CNPSiI)         P4:   Dinoflagellates (group PhytoPlankton))
#! pelagic  (CNP)            Z3:   Carnivorous mesozooplankton (group MesoZooPlankton))
#! pelagic  (CNP)            Z4:   Omnivorous mesozooplankton (group MesoZooPlankton))
#! pelagic  (CNP)            Z5:   Microzooplankton (group MicroZooPlankton))
#! pelagic  (CNP)            Z6:   Heterotrophic nanoflagellates (HNAN) (group MicroZooPlankton))
#! pelagic  (CNPSi)          R1:   Labile Organic Carbon (LOC)
#! pelagic  (C)              R2:   CarboHydrates (sugars)
#! pelagic  (CNPSi)          R6:   Particulate Organic Carbon (POC)
#! pelagic  (C)              R7:   Refractory Disoolved Organic Carbon

# Benthic variables (group BenVariables):
# ! benthic  (CNP)            Y1:   Epibenthos (group BenOrganisms))
# ! benthic  (CNP)            Y2:   Deposit feeders (group BenOrganisms))
# ! benthic  (CNP)            Y3:   Suspension feeders (group BenOrganisms))
# ! benthic  (CNP)            Y4:   Meiobenthos (group ! BenOrganisms))
# ! benthic  (CNP)            Y5:   Benthic predators (group BenOrganisms))
# ! benthic  (CNPSi)          Q1:   Labile organic carbon (group BenDetritus))
# ! benthic  (CNPSi)          Q11:  Labile organic carbon (group BenDetritus))
# ! benthic  (CNPSi)          Q6:   Particulate organic carbon (group BenDetritus))
# ! benthic  (CNP)            H1:   Aerobic benthic bacteria (group BenBacteria))
# ! benthic  (CNP)            H2:   Anaerobic benthic bacteria (group BenBacteria))
# ! benthic  (P)              K1:   Phosphate in oxic layer (group BenthicPhosphate))
# ! benthic  (P)              K11:  Phosphate in denit layer (group BenthicPhosphate))
# ! benthic  (P)              K21:  Phosphate in anoxic layer (group BenthicPhosphate))
# ! benthic  (N)              K4:   Ammonium in oxic layer (group BenthicAmmonium))
# ! benthic  (N)              K14:  Ammonium in denit layer (group BenthicAmmonium))
# ! benthic  (N)              K24:  Ammonium in anoxic layer (group BenthicAmmonium))
# ! benthic  (R)              K6:   Reduction equivalents 
# ! benthic  (M)              D1:   Oxygen penetration depth
# ! benthic  (M)              D2:   Denitrification depth 
# ! benthic  (M)              D6:   Depth distribution factor organic C 
# ! benthic  (M)              D7:   Depth distribution factor organic N
# ! benthic  (M)              D8:   Depth distribution factor organic P
# ! benthic  (M)              D9:   Depth distribution factor organic Si
# ! benthic  (O)              G2:   Benthic O2


# List of variables for analysis and visualization
vars_list = [
    'elev',
    'temp',
    'salt',
    'O2o', 
    'netPPm2',
          'N1p',
          'N3n',
          'N4n',
          'N5s',
          'N6r',
#          'B1c',
#          'Bac',
          'P1c',
          'P2c',
          'P3c',
          'P4c',
          'P5c',
          'P6c',
#	  'P1l',
#          'P2l',
#          'P3l',
#          'P4l',
 #         'P5l',
 #         'P6l',
 #         'Z2c',
 #         'Z3c',
 #         'Z4c',
 #         'Z5c',
 #         'Z6c',
 #         'R1c',
 #         'R2c',
 #         'R3c',
 #         'R6c',
 #         'RZc',
 #         'Q1c',
 #         'Q11c',
 #         'Q6c',
          'Chla',
#          'H1c',
#          'H2c',
#          'HNc',
#          'Hac',
          'Y1c',
          'Y2c',
          'Y3c',
#          'Y4c',
          'Y5c',
          'Yy3c',
#          'K6r',
#          'K16r',
#          'K26r',
#          'K5s',
#          'K15s',
#          'K3n',
#          'K4n',
#         'K13n',
#          'K14n',
#          'K24n',
#          'K1p',
#          'K11p',
#         'K21p',
#          'D1m',
#          'D2m',
#          'O3c',
#          'pCO2',
#          'CO2',
#          'HCO3',
#          'CO3',
#          'pH',
#          'Ac'
#          'G3h'
#          'G13h'
#          'G23h'
#          'G3c'
#          'G13c'
#          'G23c'
#          'G14n'
#          'Acae'
#          'Acan'
#          'DICae'
#          'DICan'
#          'pHae'
#          'pHan'
#          'pCO2ae'
#          'pCO2an'
#          'G3h'
#          'G13h'
#          'BP1c'
#          'ETW',
#          'irrenh',
#          'turenh',      
]

# Crop the file with the same xc and yc from topo file:
topo_file = Path('/export/lv9/projects/dws/model_input/bathymetry/topo_dws_500m.nc')
topo_ds = xr.open_dataset(topo_file)
xc = topo_ds['xc'].values
yc = topo_ds['yc'].values

DATA_DIR = Path('/export/lv9/projects/dws/model_output/archived_runs/spinup_02/')
FILE_PATTERN = 'dws_500m.3d.2015??.nc'

# ---------------- User settings ----------------
SAT_SAVE_DIR = Path("/export/lv9/projects/dws/results/validation/pelagic/satellite")
SAT_SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Crop bounds from topo file
XC_MIN, XC_MAX = float(xc.min()), float(xc.max())
YC_MIN, YC_MAX = float(yc.min()), float(yc.max())
print(f'Topo-derived crop bounds — xc: {XC_MIN:.0f}–{XC_MAX:.0f}, yc: {YC_MIN:.0f}–{YC_MAX:.0f}')

files = sorted(DATA_DIR.glob(FILE_PATTERN))
if not files:
    raise FileNotFoundError(f'No files found: {FILE_PATTERN} in {DATA_DIR}')

##########################################
import copernicusmarine as cm
from pathlib import Path

DATASET_ID = "cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D"

#catalogue = cm.describe(dataset_id=DATASET_ID)

import copernicusmarine as cm
from pathlib import Path

DATASET_ID = "cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D"
SAT_VAR = "CHL"  # <-- adjust if variable name differs (e.g., 'chl')

START_TIME = "2015-01-01T00:00:00"
END_TIME   = "2015-12-31T23:59:59"

catalogue = cm.describe(dataset_id=DATASET_ID)

variables = (
    catalogue.products[0]
    .datasets[0]
    .versions[0]
    .parts[0]
    .services[0]
    .variables
)

for v in variables:
    print(v.short_name, "|", v.standard_name, "|", v.units)


# ---------------- Download subset from Copernicus ----------------
# Writes NetCDF to SAT_SAVE_DIR. The file name is determined by the toolbox.

# ---------------- Reuse/open model dataset ----------------
try:
    ds
except NameError:
    files = sorted(DATA_DIR.glob(FILE_PATTERN))
    if not files:
        raise FileNotFoundError(f"No files found with pattern: {FILE_PATTERN} in {DATA_DIR}")
    ds = xr.open_mfdataset(
        files,
        combine="nested",
        concat_dim="time",
        decode_times=True,
        data_vars="minimal",
        coords="minimal",
        compat="override",
        join="override",
    )

# ---------------- Build geographic bbox from same subdomain ----------------
# Uses model coordinates and the same Y_SLICE/X_SLICE.
# Expecting lon/lat-like variables in ds.
lon_candidates = ("lonc", "lon", "longitude")
lat_candidates = ("latc", "lat", "latitude")

lon_name = next((n for n in lon_candidates if n in ds.variables), None)
lat_name = next((n for n in lat_candidates if n in ds.variables), None)

if lon_name is None or lat_name is None:
    raise KeyError(
        f"Could not find lon/lat variables in dataset. "
        f"Tried lon={lon_candidates}, lat={lat_candidates}."
    )

lon_da = ds[lon_name]
lat_da = ds[lat_name]

# Find horizontal dims from Chla if available; otherwise infer from lon/lat.
if "Chla" in ds.variables:
    chla_tmp = ds["Chla"].squeeze(drop=True)
    dims_lower = [d.lower() for d in chla_tmp.dims]
    time_dim = next((d for d in chla_tmp.dims if "time" in d.lower()), None)
    z_dim = next((d for d in chla_tmp.dims if any(k in d.lower() for k in ("level", "z", "sigma", "layer", "depth", "lev"))), None)
    xy_dims = [d for d in chla_tmp.dims if d not in (time_dim, z_dim)]
    if len(xy_dims) != 2:
        raise ValueError(f"Could not infer 2D horizontal dims from Chla dims: {chla_tmp.dims}")
    y_dim, x_dim = xy_dims
else:
    common_2d = [d for d in lon_da.dims if d in lat_da.dims]
    if len(common_2d) < 2:
        raise ValueError("Could not infer horizontal dims from lon/lat.")
    y_dim, x_dim = common_2d[-2], common_2d[-1]

# Crop the file with the same xc and yc from topo file:
topo_file = Path('/export/lv9/projects/dws/model_input/bathymetry/topo_dws_500m.nc')
topo_ds = xr.open_dataset(topo_file)
xc = topo_ds['xc'].values
yc = topo_ds['yc'].values

DATA_DIR = Path('/export/lv9/projects/dws/model_output/archived_runs/spinup_02/')
FILE_PATTERN = 'dws_500m.3d.2015??.nc'

# Crop bounds from topo file
XC_MIN, XC_MAX = float(xc.min()), float(xc.max())
YC_MIN, YC_MAX = float(yc.min()), float(yc.max())

cm.subset(
    dataset_id=DATASET_ID,
    variables=[SAT_VAR],
    minimum_longitude=XC_MIN,
    maximum_longitude=XC_MAX,
    minimum_latitude=YC_MIN,
    maximum_latitude=YC_MAX,
    start_datetime=START_TIME,
    end_datetime=END_TIME,
    output_directory=str(SAT_SAVE_DIR),
    output_filename="copernicus_satellite_chl_2015.nc",
    force_download=True,
)