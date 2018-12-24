#!/bin/bash

## Load Python 2.7.13
#module use /usrx/local/dev/modulefiles
#module load python/2.7.13

export pyPath="/usrx/local/dev/python/2.7.13/bin"
export platform=""

export myModules=${platform}"/gpfs/hps3/nos/noscrub/nwprod/csdlpy-1.5.1"
export pythonCode=${platform}"/gpfs/hps3/nos/noscrub/nwprod/metrics-1.5.1/metrics/post.py"
export logFile=${platform}"/gpfs/hps3/nos/noscrub/polar/metrics/metrics.log"

export ofsDir=${platform}"/gpfs/hps/nco/ops/com/estofs/prod/"
export basin="atl"
export stormCycle="latest"   #"2018030218"
export outputDir=${platform}"/gpfs/hps3/nos/noscrub/polar/metrics/"
export tmpDir=${platform}"/gpfs/hps3/nos/noscrub/tmp/metrics/"
export pltCfgFile=${platform}"/gpfs/hps3/nos/noscrub/nwprod/metrics-1.5.1/scripts/config.plot.metrics.R2.ini"

export ftpLogin="svinogradov@emcrzdm"
export ftpPath="/home/www/polar/estofs/metrics/"

cd ${tmpDir}
PYTHONPATH=${myModules} ${pyPath}/python -W ignore ${pythonCode} -i ${ofsDir} -s ${basin} -z ${stormCycle} -o ${outputDir} -t ${tmpDir} -p ${pltCfgFile} -u ${ftpLogin} -f ${ftpPath} # > ${logFile}
