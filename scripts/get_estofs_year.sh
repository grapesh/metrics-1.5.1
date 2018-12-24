#!/bin/bash -l
module load hpss

echo '***** GETTING ONE YEAR *****', $1

#for MONTH in 01 02 03 04 05 06 07 08 09 10 11 12; do
for MONTH in 07 08 09 10 11 12; do

YEAR=$1
PDY=$1$MONTH
./get_estofs_month.sh $PDY

done


