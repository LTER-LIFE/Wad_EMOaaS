# =============================================================================
# Setup and Imports
# =============================================================================
import xarray as xr
import numpy as np
import os
import shutil
from pathlib import Path

# =============================================================================
# User Settings
# =============================================================================

# Run this comment below to merge restart files in the terminal
# ncmerge -v /export/lv9/projects/dws/model_output/archived_runs/spinup_02/201601/restart.00??.in /export/lv9/projects/dws/model_output/archived_runs/spinup_02/restart_201601.in

# File paths (update during each iteration)
PHYS = "/export/lv9/projects/dws/model_input/hotstart/restart_dws500m_201501_hydro.in"
BIO = "/export/lv9/projects/dws/model_output/archived_runs/spinup_02/restart_201601.in"

OUT = "/export/lv9/projects/dws/model_input/hotstart/restart_201501_spinup_02.in"

# Flags: which variables to take from PHYS vs BIO
tempsalt_from_phys = 1  # 1 = take T,S from PHYS; 0 = take from BIO
spm_from_phys = 1       # 1 = take R9x from PHYS; 0 = take from BIO

# Working directory and temp files
workdir = os.path.dirname(OUT)
tmp_phys = os.path.join(workdir, "temp_phys.nc")
tmp_bio = os.path.join(workdir, "temp_bio.nc")
tmp_phys_ren = os.path.join(workdir, "temp_phys_ren.nc")
tmp_bio_last = os.path.join(workdir, "temp_bio_last.nc")

print("=" * 70)
print("Mix restart files (final-bio -> Jan2015 template):")
print(f"  PHYS (template + phys/time): {PHYS}")
print(f"  BIO  (donor final bio)     : {BIO}")
print(f"  OUTPUT                     : {OUT}")
print(f"  T,S from PHYS              : {tempsalt_from_phys}")
print(f"  R9x from PHYS              : {spm_from_phys}")
print("=" * 70)


# =============================================================================
# Helper Functions (cropping removed, only essentials kept)
# =============================================================================


def has_var(ds, var_name):
    """Check if variable exists in xarray Dataset."""
    return var_name in ds.data_vars


def first_existing_var(ds, *var_names):
    """Return first variable name that exists in dataset."""
    for var_name in var_names:
        if has_var(ds, var_name):
            return var_name
    return None


def rename_var_if_exists(ds, target_name, *alt_names):
    """Rename variable to target_name if one of the alternatives exists."""
    existing = first_existing_var(ds, target_name, *alt_names)
    if existing and existing != target_name:
        print(f"  Renaming {existing} -> {target_name}")
        ds = ds.rename({existing: target_name})
    return ds


def copy_vars_if_present(src_ds, dst_ds, var_list, verbose=True):
    """Copy variables from src to dst if they exist in src."""
    present = [v for v in var_list if has_var(src_ds, v)]
    if present:
        if verbose:
            print(f"  -> copying: {', '.join(present)}")
        dst_ds = dst_ds.update(src_ds[present])
    else:
        if verbose:
            print(f"  -> WARNING: none found in source: {', '.join(var_list)}")
    return dst_ds


def get_record_dim(ds):
    """Get the unlimited record dimension name."""
    for dim_name, dim_size in ds.dims.items():
        if dim_name in ds.encoding.get("unlimited_dims", []):
            return dim_name
    return None


print("Helper functions defined (cropping removed).")


print("\n" + "=" * 70)
print("STEP 1: Loading and cropping files")
print("=" * 70)

# Load datasets
print(f"Loading PHYS from {PHYS}...")
ds_phys = xr.open_dataset(PHYS)
print(f"  Dimensions: {dict(ds_phys.dims)}")

print(f"Loading BIO from {BIO}...")
ds_bio = xr.open_dataset(BIO)
print(f"  Dimensions: {dict(ds_bio.dims)}")

# =============================================================================
# 2) Normalize Variable Names in PHYS (TEMPORARILY DISABLED)
# =============================================================================

print("\n" + "=" * 70)
print("STEP 2: Variable renaming is temporarily disabled")
print("=" * 70)

# Keep PHYS variables exactly as loaded/cropped (no renaming).
ds_phys_ren = ds_phys.copy(deep=True)

print("No variable names were changed in PHYS.")
print(f"Variables in PHYS: {list(ds_phys_ren.data_vars.keys())}")


# =============================================================================
# 3) Select Last Record from BIO (if applicable)
# =============================================================================

print("\n" + "=" * 70)
print("STEP 3: Selecting last record from BIO")
print("=" * 70)

# Detect unlimited dimension (time dimension)
rec_dim = get_record_dim(ds_bio)
if rec_dim:
    print(f"Found unlimited record dimension: '{rec_dim}'")
    print(f"  Selecting LAST record...")
    ds_bio_last = ds_bio.isel({rec_dim: -1})
    print(f"  Selected last record. Variables: {list(ds_bio_last.data_vars.keys())}")
else:
    print("No UNLIMITED record dimension detected; using BIO as-is")
    ds_bio_last = ds_bio.copy(deep=True)


# =============================================================================
# 4) Initialize Output with PHYS as Template
# =============================================================================

print("\n" + "=" * 70)
print("STEP 4: Creating output dataset")
print("=" * 70)

# Start with PHYS as template
ds_out = ds_phys_ren.copy(deep=True)
print(f"Output initialized with PHYS template.")
print(f"  Initial variables: {list(ds_out.data_vars.keys())}")

# =============================================================================
# 5) Copy BIO Variables (excluding physical/time/coordinates)
# =============================================================================

print("\n" + "=" * 70)
print("STEP 5: Merging BIO variables into output")
print("=" * 70)

# Define variables to exclude from BIO
exclude_vars = [
    "loop", "time", "Time", "julianday", "secondsofday", "timestep",
    "xax", "yax", "zax", "lon", "lat", "longitude", "latitude", "depth", "x", "y", "z",
    "z", "zo", "U", "V", "SlUx", "Slru", "SlVx", "Slrv", "ssen", "ssun", "ssvn", "sseo", "ssuo", "ssvo",
    "Uint", "Vint", "Uadv", "Vadv", "uu", "vv", "ww", "uuEx", "vvEx", "tke", "eps", "num", "nuh", "ho", "hn"
]

# Add T,S to exclusion if taking from PHYS
if tempsalt_from_phys:
    exclude_vars.extend(["T", "S", "temp", "salt", "Temp", "Salt", "temperature", "salinity", "TEMPERATURE", "SALINITY"])

# Add R9x to exclusion if taking from PHYS
if spm_from_phys:
    exclude_vars.extend(["R9x", "r9x", "R9X", "spm", "SPM"])

# Get variables from BIO to copy (those not in exclude list)
bio_vars_to_copy = [v for v in ds_bio_last.data_vars if v not in exclude_vars]

print(f"Copying {len(bio_vars_to_copy)} BIO variables (excluding {len(exclude_vars)} physical/time/coords)...")
for var in bio_vars_to_copy:
    print(f"  -> {var}")
    ds_out[var] = ds_bio_last[var]

print(f"After BIO merge, output has {len(ds_out.data_vars)} variables.")


# =============================================================================
# 6) Force TIME/COORDS/PHYS Variables from PHYS
# =============================================================================

print("\n" + "=" * 70)
print("STEP 6: Forcing TIME/COORDS/PHYS from PHYS")
print("=" * 70)

print("\nForcing TIME from PHYS...")
ds_out = copy_vars_if_present(
    ds_phys_ren, ds_out,
    ["loop", "julianday", "secondsofday", "timestep"]
)

print("\nForcing COORDS from PHYS...")
ds_out = copy_vars_if_present(
    ds_phys_ren, ds_out,
    ["xax", "yax", "zax"]
)

print("\nForcing PHYS variables from PHYS...")
ds_out = copy_vars_if_present(
    ds_phys_ren, ds_out,
    [
        "z", "zo", "U", "SlUx", "Slru", "V", "SlVx", "Slrv",
        "ssen", "ssun", "ssvn", "sseo", "ssuo", "ssvo",
        "Uint", "Vint", "Uadv", "Vadv", "uu", "vv", "ww", "uuEx", "vvEx",
        "tke", "eps", "num", "nuh", "ho", "hn"
    ]
)

if tempsalt_from_phys:
    print("\nForcing T,S from PHYS...")
    ds_out = copy_vars_if_present(ds_phys_ren, ds_out, ["T", "S"])

if spm_from_phys:
    print("\nForcing R9x from PHYS...")
    ds_out = copy_vars_if_present(ds_phys_ren, ds_out, ["R9x"])


# =============================================================================
# 7) Ensure BIO Control Variables
# =============================================================================

print("\n" + "=" * 70)
print("STEP 7: Ensuring BIO control variables")
print("=" * 70)

ds_out = copy_vars_if_present(
    ds_bio_last, ds_out,
    ["numc", "numbc", "start_3d", "start_2d"]
)

# =============================================================================
# 8) Restore BFM Attributes on Key Variables
# =============================================================================

print("\n" + "=" * 70)
print("STEP 8: Restoring BFM attributes")
print("=" * 70)

if "R9x" in ds_out.data_vars:
    print("Adding BFM attributes to R9x...")
    ds_out["R9x"].attrs.update({
        "_FillValue": -9999.0,
        "missing_value": -9999.0,
        "type": "d3"
    })
else:
    print("R9x not found in output, skipping attribute restoration.")


# =============================================================================
# 9) Save Output File
# =============================================================================

print("\n" + "=" * 70)
print("STEP 9: Saving output")
print("=" * 70)

# Create output directory if it doesn't exist
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# Remove existing file if it exists
if os.path.exists(OUT):
    print(f"Removing existing output file: {OUT}")
    os.remove(OUT)

# Remove _FillValue and missing_value from attrs, set in encoding for R9x if present
if "R9x" in ds_out.data_vars:
    for key in ["_FillValue", "missing_value"]:
        if key in ds_out["R9x"].attrs:
            ds_out["R9x"].attrs.pop(key)
    ds_out["R9x"].encoding["_FillValue"] = -9999.0
    ds_out["R9x"].encoding["missing_value"] = -9999.0

# Save the output dataset
print(f"\nSaving output to {OUT}...")
print(f"Final output dimensions: {dict(ds_out.dims)}")
print(f"Final output variables ({len(ds_out.data_vars)}): {list(ds_out.data_vars.keys())}")

# Use netcdf4 encoding to match original file format
ds_out.to_netcdf(
    OUT,
    format="NETCDF3_CLASSIC",
    unlimited_dims=["time"] if "time" in ds_out.dims else []
)
print(f"\nSUCCESS!")
print(f"Output saved to: {OUT}")


# =============================================================================
# 10) Verify Output File (Optional)
# =============================================================================

print("\n" + "=" * 70)
print("STEP 10: Verifying output file")
print("=" * 70)

# Reload the saved file to verify
ds_verify = xr.open_dataset(OUT)
print(f"\nVerifying output file integrity:")
print(f"  Dimensions: {dict(ds_verify.dims)}")
print(f"  Variables ({len(ds_verify.data_vars)}): {list(ds_verify.data_vars.keys())}")
print(f"  Coordinates: {list(ds_verify.coords.keys())}")

# Quick checks
print(f"\nQuick checks:")
print(f"  File size: {os.path.getsize(OUT) / 1024 / 1024:.2f} MB")
print(f"  File exists: {os.path.exists(OUT)}")

print("\n" + "=" * 70)
print("DONE!")
print("=" * 70)