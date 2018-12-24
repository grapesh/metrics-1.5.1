#!/bin/bash -l
module load hpss
homedir=/gpfs/hps3/nos/noscrub/hpss/
if [ ! -d $homedir ]; then
   mkdir $homedir
fi
basedir='/NCEPPROD/2year/hpssprod/runhistory'
filename=gpfs_hps_nco_ops_com_estofs_prod_estofs_atl

for PDY in 20181113; do
#for PDY in 20171013 20171014 20171029 20171030 20171110 20171111 20180117 20180118 20180228 20180301 20180302 20180303 20180304 20180305 20180312 20180313 20180423 20180424; do
YEAR=`echo $PDY | cut -c 1-4`
MONTH=`echo $PDY | cut -c 5-6`
echo $YEAR $MONTH
basedir=/NCEPPROD/2year/hpssprod/runhistory/rh${YEAR}/${YEAR}${MONTH}
for cyc in 00 06 12 18; do

tarfile=$filename.${PDY}${cyc}.output.tar
hsi get $basedir/$PDY/$tarfile

tmpdir=${homedir}/${PDY}
if [ ! -d $tmpdir ]; then
   mkdir $tmpdir
fi
tar -xvf $tarfile
mv estofs.atl.*.points.*.nc $tmpdir/.
rm -r tmpnwprd1 *.nc *.grib2 $tarfile

done
done

