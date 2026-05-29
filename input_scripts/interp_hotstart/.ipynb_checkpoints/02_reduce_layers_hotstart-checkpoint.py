#! /usr/bin/env python

# to run on terminal interactively
# source .bashrc.conda3
# conda activate interp_hotstart

# python script to read an .nc file and reduce number of layers 
# and write
# a new file
# Works on a restart file

# import the relevant packages
import sys
sys.path.append('/share/apps/python2.6.6/lib/python2.6/site-packages/pynetcdf')
from netCDF4 import Dataset
#from NetCDF import *
from numpy import *
from pylab import *
#import Numeric
#from ncvue import ncvue

# Access MinIO files
from minio import Minio

# Configuration (do not containerize this cell)
param_minio_endpoint = "scruffy.lab.uvalight.net:9000"
param_minio_user_prefix = "zhanqing2016@gmail.com"  # Your personal folder in the naa-vre-user-data bucket in MinIO
secret_minio_access_key = ""
secret_minio_secret_key = ""

# mc = Minio(endpoint=param_minio_endpoint,
#           access_key=secret_minio_access_key,
#           secret_key=secret_minio_secret_key)

# List existing buckets: get a list of all available buckets
# mc.list_buckets()

# List files in bucket: get a list of files in a given bucket. For bucket `naa-vre-user-data`, only list files in your personal folder
# objects = mc.list_objects("naa-vre-user-data", prefix=f"{param_minio_user_prefix}/")
#for obj in objects:
#    print(obj.object_name)

# Upload file to bucket: uploads `myfile_local.csv` to your personal folder on MinIO as `myfile.csv`
#mc.fput_object(bucket_name="naa-vre-user-data", 
#               file_path="/export/lv1/user/jvandermolen/model_output/active_runs/boundaries/dws_200m_nwes/restart_201501_hydro.nc", 
#               object_name=f"{param_minio_user_prefix}/restart_201501_hydro.nc")

# Download file from bucket: download `myfile.csv` from your personal folder on MinIO and save it locally as `myfile_downloaded.csv`
# mc.fget_object(bucket_name="naa-vre-user-data", object_name=f"{param_minio_user_prefix}/PCLake_PLoads.png", file_path="/export/lv9/user/qzhan/home/PCLake_PLoads.png")

############## settings ##################################################

# Reduce vertical layers by grouping this many source layers into one target layer.
LAYER_REDUCTION_FACTOR = 3

# from script nest_bdy
#infname=os.environ['infname']
#ofname=os.environ['ofname']

# set hard (comment out if using script)
# For the hydro file
#infname='/export/lv1/user/jvandermolen/model_output/active_runs/boundaries/dws_200m_nwes/restart_201501_hydro.nc'
#ofname='/export/lv9/user/qzhan/model_output/active_runs/boundaries/dws_200m_nwes/restart_201501_hydro_10layers.nc'

# For the bio file
infname='/export/lv9/user/qzhan/model_output/active_runs/boundaries/dws_200m_nwes/restart_201501_dws200m_bio.nc'
ofname='/export/lv9/user/qzhan/model_output/active_runs/boundaries/dws_200m_nwes/restart_201501_bio_10layers.nc'

##################################################################################
# Main routine

# Open input files
print('reducing layers in nc file.')
print('Input files:')
print(infname)
infile=Dataset(infname,'r',format='NETCDF4') #NetCDFFile(infname,'r')

# Launch the ncview-like GUI
#ncvue(infname) # or on cluster ncview(infname) if X11 forwarding is enabled

print('Output file: ',ofname)

# get dimensions and variables from file
alldimnames=list(infile.dimensions.keys())
varnames=list(infile.variables.keys())
print('Variables: ',varnames)

# open and initialise output file
#outfile=NetCDFFile(ofname,'w')
outfile=Dataset(ofname,'w',format='NETCDF3_CLASSIC')
ndims=len(alldimnames)
for idim in range(ndims):
  dimname=alldimnames[idim]
  print(dimname)
  dimvalue=infile.dimensions[alldimnames[idim]]
  print('dimvalue', dimvalue)

  if alldimnames[idim] == 'zax':
    lendim=1+(len(dimvalue)-1)//LAYER_REDUCTION_FACTOR
  else:
    lendim=len(dimvalue)

  outfile.createDimension(alldimnames[idim],lendim)

# process

for varname in varnames:
  # read variable
  print(varname)
  var=infile.variables[varname]
  dimnames=var.dimensions
  datavals=var[:]
#  data_attlist=dir(var)
  datatype=datavals.dtype.kind
##  print datatype
#  if datatype=='f':
#    datatype='d'
#  if ('_FillValue' in data_attlist):  
#    mv=getattr(var,'_FillValue')
#  else:
#    if ('missing_value' in data_attlist):  
#       mv=getattr(var,'missing_value')
#    else:
#       mv=None

#  print(data_attlist)
  # save time variable
  if varname=='timestemp':
    time_2d=datavals
    time_2d_units=getattr(var, 'units', None)

  if len(dimnames)==3:
    # adjust
    sv=shape(datavals)
    nout=1+(sv[0]-1)//LAYER_REDUCTION_FACTOR
    out=zeros((nout,sv[1],sv[2]))
    if varname=='ho' or varname=='hn' :   # add grouped levels
      out[0,:,:]=datavals[0,:,:]
      for nl in range(1,nout):
        start=1+(nl-1)*LAYER_REDUCTION_FACTOR
        stop=start+LAYER_REDUCTION_FACTOR
        out[nl,:,:]=sum(datavals[start:stop,:,:], axis=0)
    else:                                         # average grouped levels
      out[0,:,:]=datavals[0,:,:]
      for nl in range(1,nout):
        start=1+(nl-1)*LAYER_REDUCTION_FACTOR
        stop=start+LAYER_REDUCTION_FACTOR
        out[nl,:,:]=mean(datavals[start:stop,:,:], axis=0)
  else:
    out=datavals

  if varname=='zax':
    print('yes')
    sv=datavals.shape
    newz=1+(sv[0]-1)//LAYER_REDUCTION_FACTOR
    out=arange(newz, dtype=datavals.dtype)
  #out = np.arange(16, dtype=datavals.dtype)

  # write variable
#  outvar=outfile.createVariable(varnames[j],datatype,dimnames,fill_value=mv,chunksizes=out.shape)

  print(out)
  outvar=outfile.createVariable(varname,datatype,dimnames,chunksizes=out.shape)
  sout=list(shape(out))
  print(sout)
  outvar[:]=out
  #if len(sout)>1:
  #  outvar[:]=out
   

  #else:
  #  print(outvar[:])
  #  print(sout)
  #  print(out)
  #  outvar[:]=out
  #  print(not(sout))
  #  if not(sout):
  #    outvar[:]=out
   # else:
   #   outvar[:]=out

  ##units and other attributes should be written as well!!
  # copy attributes
  for att in var.ncattrs():
    if (att!='_FillValue') & (att!='assignValue') & (att!='getValue') & (att!='typecode'):
      setattr(outvar,att,getattr(var,att))
  
# close files  
infile.close()
outfile.close()

print('Done')


