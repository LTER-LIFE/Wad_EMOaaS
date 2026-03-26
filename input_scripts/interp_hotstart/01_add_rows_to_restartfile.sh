#!/bin/bash

# adds rows to restart file 
# used to make restart file match a particular subdomain decomposition

#--------------- settings --------------------------
module load netcdf/4.6.1

indir=/export/lv1/user/jvandermolen/model_output/active_runs/boundaries/dws_200m_nwes
outdir=/export/lv9/user/qzhan/model_output/active_runs/boundaries/dws_200m_nwes

infname=restart_201501_dws200m_bio.nc.keep
outfname=restart_201501_dws200m_bio.nc

addrows=10   # number of rows to add

#--------------------------------------------------------------------- 

cp $indir/$infname $outdir/restart.in

# add rows at the bottom
echo "preparing..."
# first copy the bottom row to a file
ncks --no-abc -O -d yax,1 $indir/$infname $outdir/temp_slice.nc
# then stick it to the output file
# then combine
ncrename -h -d yax,time $outdir/temp_slice.nc                                       #rename dimension
ncpdq -O -a time,xax,zax $outdir/temp_slice.nc $outdir/temp_slice1.nc               #move time dimension to front
ncks --no-abc -O --mk_rec_dmn time $outdir/temp_slice1.nc $outdir/temp_slice2.nc    # make it the record dimension
ncrename -h -d yax,time $outdir/restart.in                                           # do the same for the file produced so far
ncpdq -O -a time,xax,zax $outdir/restart.in $outdir/temp_out1.nc
ncks --no-abc -O --mk_rec_dmn time $outdir/temp_out1.nc $outdir/temp_out2.nc
echo "adding rows"
ncrcat -O $outdir/temp_slice2.nc $outdir/temp_out2.nc $outdir/temp_combined.nc      # combine along new 'time' dimension
#for i in {2..$addrows} ; do
for (( i = 1 ; i < $addrows; i++ )); do
  echo "i="$i
  mv $outdir/temp_combined.nc $outdir/temp_combined2.nc
  ncrcat -O $outdir/temp_slice2.nc $outdir/temp_combined2.nc $outdir/temp_combined.nc      # combine along new 'time' dimension
done
ncrename -h -d time,yax $outdir/temp_combined.nc                                    # rename back
ncpdq -O -a zax,yax,xax $outdir/temp_combined.nc $outdir/$outfname                  # put order back
# now zax is the record dimension, not sure how to downgrade that, maybe not needed.

# clean up
echo "cleaning up"
rm $outdir/restart.in
rm $outdir/temp_slice.nc
rm $outdir/temp_slice1.nc
rm $outdir/temp_slice2.nc
rm $outdir/temp_out1.nc
rm $outdir/temp_out2.nc
rm $outdir/temp_combined.nc
rm $outdir/temp_combined2.nc

module unload netcdf/4.6.1
echo "Done"
