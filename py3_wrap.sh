#!/usr/bin/env bash
source /ihome/crc/install/lmod/lmod/init/bash
module purge
module load python/3.7.0
python $@
