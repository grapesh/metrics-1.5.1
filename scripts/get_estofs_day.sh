#!/bin/bash -l
module load hpss
homedir=/gpfs/hps3/nos/noscrub/hpss/
if [ ! -d $homedir ]; then
   mkdir $homedir
fi
basedir='/NCEPPROD/2year/hpssprod/runhistory'
filename=gpfs_hps_nco_ops_com_estofs_prod_estofs_atl

for PDY in $1; do
YEAR=`echo $PDY | cut -c 1-4`
MONTH=`echo $PDY | cut -c 5-6`
DAY=`echo $PDY | cut -c 7-8`

echo '**** GETTING ONE DAY **** : ' $YEAR $MONTH $DAY

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

tarfile=$tmpdir/../estofs.atl.$1.tar.gz
echo 'Creating tar file ' $tarfile
tar -zcvf $tarfile -C $tmpdir .

rm $tmpdir/$1
scp $tarfile svinogradov@emcrzdm:/home/ftp/polar/estofs/.

done

