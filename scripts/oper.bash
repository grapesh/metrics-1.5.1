#!/bin/bash

## Load Python 2.7.13
#module use /usrx/local/dev/modulefiles
#module load python/2.7.13

export pyPath="/usrx/local/dev/python/2.7.13/bin"
export pyPath="/Users/svinogra/anaconda/bin/"
export platform="/users/svinogra/mirrors/wcoss/surge"
#export platform=""

export myModules=${platform}"/gpfs/hps3/nos/noscrub/nwprod/csdlpy-1.5.1"
export pythonCode=${platform}"/gpfs/hps3/nos/noscrub/nwprod/metrics-1.5.1/metrics/oper.py"
export logFile=${platform}"/gpfs/hps3/nos/noscrub/polar/metrics/oper.log"

export modelName="estofs_atl"
export PDY=$1   #"20180110"

export ofsDir=${platform}"/gpfs/hps/nco/ops/com/estofs/prod/"${modelName}
#export ofsDir=${platform}"/gpfs/hps3/nos/noscrub/hpss/"
export maxLeadHours="178"
export dbDir=${platform}"/gpfs/hps3/nos/noscrub/db_skill/"

cd ${tmpDir}
PYTHONPATH=${myModules} ${pyPath}/python -W ignore ${pythonCode} -i ${ofsDir} -z ${PDY} -m ${maxLeadHours} -d ${dbDir} -n ${modelName} # > ${logFile}
