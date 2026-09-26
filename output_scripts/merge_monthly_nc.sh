#!/bin/bash

YEAR=$1

if [ -z "$YEAR" ]; then
    echo "Usage: $0 YEAR"
    echo "Example: $0 2025"
    exit 1
fi

for MM in [0-1][0-9]; do

    outfile="dws_500m.2d.${YEAR}${MM}.nc"

    # Skip if output already exists
    if [ -f "$outfile" ]; then
        echo "Skipping 2d $MM -> $outfile already exists"
        continue
    fi

    files="${MM}/dws_500m.2d.0"*.nc

    if ls $files >/dev/null 2>&1; then
        echo "Merging 2d $MM -> $outfile"
        if ncmerge $files "$outfile"; then
          echo "Merge successful, deleting source files..."
          rm -f $files
        else
          echo "Merge failed for month $MM"
        fi
    fi
done

for MM in [0-1][0-9]; do

    outfile="dws_500m.3d.${YEAR}${MM}.nc"

    # Skip if output already exists
    if [ -f "$outfile" ]; then
        echo "Skipping 3d $MM -> $outfile already exists"
        continue
    fi

    files="${MM}/dws_500m.3d.0"*.nc

    if ls $files >/dev/null 2>&1; then
        echo "Merging 3d $MM -> $outfile"
        if ncmerge $files "$outfile"; then
          echo "Merge successful, deleting source files..."
          rm -f $files
        else
          echo "Merge failed for month $MM"
        fi
    fi
done

echo "Done."