#!/bin/bash -l
module load hpss

echo '***** GETTING ONE MONTH ***** ' $1

for DY in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31; do

YEAR=`echo $PDY | cut -c 1-4`
MONTH=`echo $PDY | cut -c 5-6`
PDY=$1$DY
./get_estofs_day.sh $PDY

done

