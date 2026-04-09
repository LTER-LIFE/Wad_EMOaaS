#! /usr/bin/env python
##! /usr/bin/env python

# python script to make a movie of a GETM variable

# Johan van der Molen, apr 2024, after make_particle_movie.py.

# import the relevant packages
import sys, os, glob
sys.path.append('/export/lv1/user/jvandermolen/home/python_scripts/plot_coastline')
sys.path.append('/export/lv1/user/jvandermolen/home/python_scripts/plot_trajectories')
sys.path.append('/export/lv1/user/jvandermolen/home/python_scripts/polygon_tools')
from netCDF4 import Dataset
from numpy import *
from pylab import *
from plot_coastline import plot_coast
from time import sleep
from datetime import *
from xlrd import *

################# settings ##########################################################

#indir='/export/lv1/user/jvandermolen/model_output/archived_runs/nwes_summer2023/2023/06/'
#fname='north_west_european_shelf.3d.subset.nc'
indir='/export/lv9/ERSEM_runs/nwes_hindcast_2025/20x16/'
fname='north_west_european_shelf_bfm_jan2025.3d.nc'
outdir='/export/lv1/user/jvandermolen/model_output/active_runs/movie/'

dt=1  # display every dt time step in a frame

#area=[-6.0, 16.5, 48.0, 60.5]  #North Sea
#area=[-17.5, 13.2, 46.4, 63.0]  #shelf
#area=[-3.0, 9.0, 51.0, 56.7]    #Southern Bight
#area=[-11.5,-1.2,48.3,54.2]    # Scilly Isles, wider area
#area=[-5.0, 13.0, 49.0, 62.5]  #North Sea
#area=[4.0, 9.0, 53.0, 55.5]  #Wadden Sea
#area=[4.5, 7.0, 53.0, 54.0]  #Dutch Wadden Sea

index_lon_transect=258
lat_start=100
lat_stop=335 #358
area=[46.6,63.0,-300,2,]

max_scale=1500.

#nt_start=714  #390
#nt_stop=715 #300 #100

yy_start=2010
yy_stop=2022
mm_start=1
mm_stop=12
daystep=4   # 4 for pelagic, 8 for benthic vars

# for coastline
gridfname='/export/lv1/user/jvandermolen/home/GETM_ERSEM_SETUPS/north_west_european_shelf/topo.nc'
coast_mode=2   # 1: coastline file, 2: zero depth contour
lwc=1

layer=24
plotvar='O2o'
# K1p K11p K21p K4n K14n K24n K5s K15s K6r K3n K13n K23n 

#-------------------------------------------------------------------------------------

if plotvar=='Q6c':
  vmin=1E5
  vmax=2E6
  colormap='nipy_spectral' #'rainbow'

if plotvar=='netPPm2':
  vmin=0
  vmax=10000
  colormap='YlGn' #'rainbow'

if plotvar=='jsurO3c':
  vmin=-2000
  vmax=2000
  colormap='seismic' #'rainbow'

if plotvar=='Y1c':
  vmin=0
  vmax=3000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Y2c':
  vmin=0
  vmax=40000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Y3c':
  vmin=0
  vmax=50000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Y4c':
  vmin=0
  vmax=250
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Y5c':
  vmin=0
  vmax=7000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='O2o':
  layer=1
  vmin=100
  vmax=450
  colormap='nipy_spectral' #'rainbow'

if plotvar=='pH':
  vmin=6
  vmax=9
  colormap='nipy_spectral' #'rainbow'

if plotvar=='D1m':
  vmin=0
  vmax=0.02
  colormap='nipy_spectral' #'rainbow'

if plotvar=='D2m':
  vmin=0
  vmax=0.05
  colormap='nipy_spectral' #'rainbow'

if plotvar=='N3n':
  vmin=0
  vmax=150
  colormap='nipy_spectral' #'rainbow'

if plotvar=='N1p':
  vmin=0
  vmax=6
  colormap='nipy_spectral' #'rainbow'

if plotvar=='N5s':
  vmin=0
  vmax=100
  colormap='nipy_spectral' #'rainbow'

if plotvar=='N4n':
  vmin=0
  vmax=15
  colormap='nipy_spectral' #'rainbow'

if plotvar=='ESS':
  vmin=0
  vmax=30000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Chla':
  vmin=0
  vmax=100
  colormap='nipy_spectral' #'rainbow'

if plotvar=='DIC':
  vmin=0
  vmax=2500
#  layer=1   #activate for bottom
  colormap='nipy_spectral' #'rainbow'

if plotvar=='R1c':
  vmin=0
  vmax=750
  colormap='nipy_spectral' #'rainbow'

if plotvar=='R2c':
  vmin=0
  vmax=35000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='R6c':
  vmin=0
  vmax=50000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Z2c':
  vmin=0
  vmax=150
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Z3c':
  vmin=0
  vmax=150
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Z4c':
  vmin=0
  vmax=150
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Z5c':
  vmin=0
  vmax=75
  colormap='nipy_spectral' #'rainbow'

if plotvar=='P1c':
  vmin=0
  vmax=3000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='P2c':
  vmin=0
  vmax=500
  colormap='nipy_spectral' #'rainbow'

if plotvar=='P3c':
  vmin=0
  vmax=500
  colormap='nipy_spectral' #'rainbow'

if plotvar=='P4c':
  vmin=0
  vmax=200
  colormap='nipy_spectral' #'rainbow'

if plotvar=='P5c':
  vmin=0
  vmax=750
  colormap='nipy_spectral' #'rainbow'

if plotvar=='P6c':
  vmin=0
  vmax=2000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='BP1c':
  vmin=0
  vmax=5000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='TMLd':
  vmin=-150
  vmax=0
  colormap='nipy_spectral' #'rainbow'

if plotvar=='RZc':
  layer=1
  vmin=0
#  vmax=600 #surface
  vmax=1500 #bottom
  colormap='nipy_spectral' #'rainbow'

if plotvar=='salt':
  vmin=30
  vmax=36
  colormap='nipy_spectral' #'rainbow'

if plotvar=='temp':
  layer=1
  vmin=-2
  vmax=23
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K1p':
  vmin=0
  vmax=30
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K11p':
  vmin=0
  vmax=100
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K21p':
  vmin=0
  vmax=300
  colormap='nipy_spectral' #'rainbow'

if plotvar=='jbotN1p':
  vmin=-2.5
  vmax=2.5
  colormap='seismic' #'rainbow'

if plotvar=='jbotN3n':
  vmin=-1
  vmax=1
  colormap='seismic' #'rainbow'

if plotvar=='jbotN4n':
  vmin=-1
  vmax=1
  colormap='seismic' #'rainbow'

if plotvar=='jbotN5s':
  vmin=-5
  vmax=5
  colormap='seismic' #'rainbow'

if plotvar=='Ac':
  vmin=0
  vmax=2200
  colormap='nipy_spectral' #'rainbow'

if plotvar=='xEPS':
  vmin=0
  vmax=5
  colormap='nipy_spectral' #'rainbow'

if plotvar=='B1c':
  vmin=0
  vmax=75
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Bac':
  vmin=0
  vmax=10
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Hs_out':
  vmin=0
  vmax=7
  colormap='nipy_spectral' #'rainbow'

if plotvar=='Tz_out':
  vmin=0
  vmax=10
  colormap='nipy_spectral' #'rainbow'

if plotvar=='u_orb_out':
  vmin=0
  vmax=1.5
  colormap='nipy_spectral' #'rainbow'

if plotvar=='eta_out':
  vmin=0
  vmax=0.1
  colormap='nipy_spectral' #'rainbow'

if plotvar=='H1c':
  vmin=0
  vmax=350
  colormap='nipy_spectral' #'rainbow'

if plotvar=='H2c':
  vmin=0
  vmax=30000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='HNc':
  vmin=0
  vmax=500
  colormap='nipy_spectral' #'rainbow'

if plotvar=='TauC':
  vmin=0
  vmax=4
  colormap='nipy_spectral' #'rainbow'

if plotvar=='TauW':
  vmin=0
  vmax=10
  colormap='nipy_spectral' #'rainbow'

if plotvar=='ws_out':
  vmin=-0.002
  vmax=0
  colormap='nipy_spectral' #'rainbow'

if plotvar=='CO3':
  vmin=0
  vmax=800
  colormap='nipy_spectral' #'rainbow'

if plotvar=='HCO3':
  vmin=0
  vmax=2000
  colormap='nipy_spectral' #'rainbow'

if plotvar=='tke':
  vmin=0
  vmax=0.005
  colormap='nipy_spectral' #'rainbow'

if plotvar=='num':
  vmin=0
  vmax=0.05
  colormap='nipy_spectral' #'rainbow'

if plotvar=='nuh':
  vmin=0
  vmax=0.05
  colormap='nipy_spectral' #'rainbow'

if plotvar=='diss':
  vmin=0
  vmax=0.00005
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K1p':
  vmin=0
  vmax=50
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K11p':
  vmin=0
  vmax=250
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K21p':
  vmin=0
  vmax=400
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K3n':
  vmin=0
  vmax=1.1
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K13n':
  vmin=0
  vmax=0.8
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K23n':
  vmin=0
  vmax=0.3
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K5s':
  vmin=0
  vmax=35
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K15s':
  vmin=0
  vmax=175
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K4n':
  vmin=0
  vmax=0.8
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K14n':
  vmin=0
  vmax=3
  colormap='nipy_spectral' #'rainbow'

if plotvar=='K24n':
  vmin=0
  vmax=30
  colormap='nipy_spectral' #'rainbow'

if plotvar=='EIR':
  vmin=0
  vmax=500
  colormap='nipy_spectral' #'rainbow'


fs=10

################## Subroutines #######################################################

def make_movie(indir,fname,yy_start,yy_stop,mm_start,mm_stop,step):
# main callable routine

  nt_tot=0
  for yy in range(yy_start,yy_stop+1):
    for mm in range(mm_start,mm_stop+1):
      if mm<10:
        monthstring='0'+str(mm)
      else:
        monthstring=str(mm)
      # open file and read data
      file=Dataset(indir+'/'+str(yy)+'/'+monthstring+'/'+fname,'r',format='NETCDF4')
      var=file.variables['time']
      time=var[:]
      time_units=var.units
      ntimesteps=len(time)
      print(ntimesteps)
#      if (ntimesteps<nt_stop):
      nt_start=1
      nt_stop=ntimesteps

      var=file.variables['latc']
      lat=var[:]
      dlat=lat[2]-lat[1]
      lat=lat-dlat

      var=file.variables['lonc']
      lon=var[:]
      dlon=lon[2]-lon[1]
      lon=lon-dlon

      var=file.variables['h']
      hdumdum=var[:]
      sh=shape(hdumdum)
      print(sh)
      hdum=ma.masked_array.filled(hdumdum)
      h=1*hdum[:,:,lat_start:lat_stop,index_lon_transect]
      latplot=squeeze(1*h[0,:,:])
#      h[:,-1,:]=0.5*hdum[:,-1,lat_start:lat_stop,index_lon_transect]
      latplot[-1,:]=lat[lat_start:lat_stop]
#      print(lat[lat_start:lat_stop])
#      sys.exit()
      for i in reversed(range(sh[1]-1)):
#        print('i',i)
#        h[:,i,:]=h[:,i+1,:]+0.5*hdum[:,i+1,lat_start:lat_stop,index_lon_transect]+0.5*hdum[:,i,lat_start:lat_stop,index_lon_transect]
        h[:,i,:]=h[:,i+1,:]+hdum[:,i,lat_start:lat_stop,index_lon_transect]#        print('h',h[1,i,1])
        latplot[i,:]=lat[lat_start:lat_stop]
      # overwrite masked value at bottom
      h[:,0,:]=h[:,1,:]+0.5*hdum[:,1,lat_start:lat_stop,index_lon_transect]
#      print('h',h[1,0,1])
#      print(latplot[0,:])
#      sys.exit()

      var=file.variables[plotvar]
      dummy=var[:]
      varunits=var.units
      longname=var.long_name
      print('longname',longname)
      var=file.variables['bathymetry']
      dumdumbath=var[:]
      dumbath=ma.masked_array.filled(dumdumbath)
      if len(shape(dummy))==4:
        plvar=dummy[:,:,lat_start:lat_stop,index_lon_transect]
        bathprof=squeeze(dumbath[lat_start:lat_stop,index_lon_transect])
      else:
        plvar=dummy[:,:,:]
  
      # read cruise tracks
#      [ctime,clon,clat]=read_cruise_track('ActNow_survey_tracks.xlsx')

      # plot
      files=[]
      figure(1,(10,7),None,facecolor='w',edgecolor='k')
      for nt in range(nt_start,nt_stop,daystep):
    #  for nt in range(5):
        clf()
#        subplot(1,1,1,aspect=1.5)
        subplot(1,1,1)
        tt=getm_time_to_datetime(time[nt],time_units)
        print(time[nt])
        print(tt)
        print(datetime2string(tt))
        print(shape(h))
        print(shape(bathprof))
#        vertcord=flipud(h[nt,:,:])-bathprof
        vertcord=-h[nt,:,:]+h[nt,1,:]-bathprof
        figtitle=plotvar+' '+datetime2string(tt)+' longitude '+str(lon[index_lon_transect])
        plot_trans(latplot,vertcord,plvar[nt,:,:],area,figtitle,longname,varunits)
        plot(latplot[0,:],-bathprof,'-k')
#        show()
#        sys.exit()
#        if coast_mode==1:
#          plot_coast(lwc)
#        else:
#          plot_coast_contour()
#        axis(area)
        print('saving figure...')
        ofname=outdir+'_tmp%03d.png'%nt_tot
        if os.path.isfile(ofname):
          os.remove(ofname)          #clean up first
        savefig(ofname,dpi=200)
        sleep(1.0)
        files.append(ofname)
        nt_tot=nt_tot+1

#  print 'Making movie file - this may take a while'
#  os.system("mencoder 'mf://_tmp*.png' -mf type=png:fps=10 \
#     -ovc lavc -lavcopts vcodec=wmv2 -oac copy -o animation.mpg")

  # cleanup
#  for fname in files: os.remove(fname)

      file.close()

  return

#--------------------------------------------------------------------------------------

def plot_coast_contour():

  file=Dataset(gridfname,'r',format='NETCDF4')
  var=file.variables['lat']
  lat=var[:] #.getValue()
  var=file.variables['lon']
  lon=var[:] #.getValue()
  var=file.variables['bathymetry']
  bathy=var[:]
  file.close()

  landmask=where(bathy<0,0,1)

  levs=[0.5]                         # coast line
  cs2=contour(lon,lat,landmask,levs,colors='k',alpha=0.5)
  zc=cs2.collections[0]
  setp(zc,linewidth=1)

  return

#-------------------------------------------------------------------------------------

def plot_map(lat,lon,var,area,figtitle,varname,unit):

#  C=contourf(lon,lat,var,fontsize=fs-1)
  C=pcolormesh(lon,lat,var,vmin=vmin,vmax=vmax,cmap=colormap)
  cbar=colorbar(C,fraction=0.0335,pad=0.03)
  cbar.set_label(varname+'['+unit+']',rotation=270,labelpad=15)

  axis(area)
  title(figtitle,fontsize=fs+2)
  xlabel('Longitude')
  ylabel('Latitude')

  return

#-------------------------------------------------------------------------------------

def plot_trans(lat,h,var,area,figtitle,varname,unit):

#  C=contourf(lon,lat,var,fontsize=fs-1)
  C=pcolormesh(lat,h,var,vmin=vmin,vmax=vmax,cmap=colormap)
  cbar=colorbar(C,fraction=0.0335,pad=0.03)
  cbar.set_label(varname+'['+unit+']',rotation=270,labelpad=15)
#  print(shape(lat))
#  print(shape(h))
#  print(shape(var))
#  print(min(lat.flatten()))
#  print(max(lat.flatten()))

  

  axis([min(lat.flatten()),max(lat.flatten()),min(h.flatten()),0],'auto')
  title(figtitle,fontsize=fs+2)
  xlabel('Latitude')
  ylabel('Depth')

  return


#-------------------------------------------------------------------------------------

def getm_time_to_datetime(t,units):
  # converts scalar t in GETM time format to datetime object
  startdate=units[-19:]
  dstart=datestring2datetime(startdate)
  dtime=dstart+timedelta(seconds=int(t))

  return dtime

#-----------------------------------------------------------------------------

def datestring2datetime(dstr):
# converts a date string to datetime object

  yy=int(dstr[0:4])
  mm=int(dstr[5:7])
  dd=int(dstr[8:10])
  hh=int(dstr[11:13])
  mn=int(dstr[14:16])
  ss=int(dstr[17:19])
  d=datetime(yy,mm,dd,hh,mn,ss)

  return d

#-----------------------------------------------------------------

def datetime2string(d):
# converts a datetime object to 2 letter strings

  if len(str(d.month))==1:
     mm='0'+str(d.month)
  else:
     mm=str(d.month)
  if len(str(d.day))==1:
     dd='0'+str(d.day)
  else:
     dd=str(d.day)
  if len(str(d.hour))==1:
     hh='0'+str(d.hour)
  else:
     hh=str(d.hour)
  if len(str(d.minute))==1:
     mmm='0'+str(d.minute)
  else:
     mmm=str(d.minute)
  if len(str(d.second))==1:
     ss='0'+str(d.second)
  else:
     ss=str(d.minute)

  timestring=str(d.year)+'-'+mm+'-'+dd+' ' #+hh+':'+mmm+':'+ss

  return timestring

#-----------------------------------------------------------------

def read_cruise_track(xlsfile):

  wb=open_workbook(xlsfile)
  sheet=wb.sheet_by_index(0)  
  dummy=sheet.col_values(1)
  hh=dummy[2:]
  dummy=sheet.col_values(2)
  mmm=dummy[2:]
  dummy=sheet.col_values(3)
  clat=array(dummy[2:])
  dummy=sheet.col_values(4)
  clon=array(dummy[2:])
  dummy=sheet.col_values(7)
  dd=dummy[2:]
  dummy=sheet.col_values(8)
  mm=dummy[2:]
  dummy=sheet.col_values(9)
  yy=dummy[2:]

  for ii in range(len(yy)):
    ct=datetime(int(yy[ii]),int(mm[ii]),int(dd[ii]),int(hh[ii]),int(mmm[ii]))
#    print(ct)
    if ii==0:
      ctime=array(ct)
#      print(ii,ctime)
    else:
      ctime=concatenate((ctime,ct),axis=None)
#      print(ctime)
#      sys.exit()


#  print(shape(ctime))
#  print(shape(clon))
#  print(shape(clat))
#  sys.exit()
  return ctime,clon,clat

################## Main ##############################################################

#for filename in glob.glob('_tmp*.png'):
#  os.remove(filename)

# main just for testing call to main function
make_movie(indir,fname,yy_start,yy_stop,mm_start,mm_stop,step)

#show()
     
