#!/usr/bin/env bash

#############################################################
# CMSSW setup
# Based on https://github.com/cms-tau-pog/NanoProd/blob/main/env.sh
#
# Author(s): Raghav Kansal
#############################################################

CMSSW_VER=CMSSW_14_2_2
this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
this_dir="$( cd "$( dirname "$this_file" )" && pwd )"

run_cmd() {
  "$@"
  RESULT=$?
  if (( $RESULT != 0 )); then
    echo "Error while running '$@'"
    exit $RESULT
  fi
}

run_cmd source /cvmfs/cms.cern.ch/cmsset_default.sh

if ! [ -f "$this_dir/cmssw/$CMSSW_VER/.installed" ]; then
    run_cmd mkdir -p "$this_dir/cmssw"
    run_cmd cd "$this_dir/cmssw"
    if [ -d $CMSSW_VER ]; then
      echo "Removing incomplete $CMSSW_VER installation..."
      run_cmd rm -rf $CMSSW_VER
    fi
    echo "Creating $CMSSW_VER area in $PWD ..."
    run_cmd scramv1 project CMSSW $CMSSW_VER
    run_cmd cd $CMSSW_VER/src
    run_cmd eval `scramv1 runtime -sh`

    # no need to install patches

    # custom code
    # not sure why, but this directory structure is necessary...
    run_cmd mkdir -p DAZSLE/DAZSLE
    run_cmd ln -s "$this_dir/customizations" DAZSLE/DAZSLE/python

    run_cmd scram b -j8
    run_cmd cmsenv
    run_cmd cd "$this_dir"
    run_cmd touch "$this_dir/cmssw/$CMSSW_VER/.installed"
else
    run_cmd cd "$this_dir/cmssw/$CMSSW_VER/"
    run_cmd cmsenv
    run_cmd cd ../..
fi