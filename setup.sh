#!/usr/bin/env bash

#############################################################
# CMSSW setup — CHS campaign (NanoAODv17ScoutingCHS24)
#
# Builds CMSSW_16_1_0_pre4 with:
#   1. Jan Schulte's derivedScouting topic (CHS jets + 6-class
#      scouting UParT + ONNX models)
#   2. the HHbbtt ScoutingNanoProduction fork (production psets
#      with the baked preselection + whitelist)
#
# Prerequisites (one-time):
#   git config --global user.github <your-github-username>
#   (needed by git cms-merge-topic)
#
# Usage:  ./setup.sh          # first run builds (~15-25 min), later runs just cmsenv
#############################################################

CMSSW_VER="${CMSSW_VERSION:-CMSSW_16_1_0_pre4}"
SCOUT_FORK="${SCOUT_FORK:-https://github.com/ArghyaRanjanDas/ScoutingNanoProduction.git}"
SCOUT_BRANCH="${SCOUT_BRANCH:-hhbbtt-chs-integration}"
DERIVED_TOPIC="${DERIVED_TOPIC:-JanFSchulte:derivedScouting}"

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
    if ! git config --get user.github > /dev/null; then
      echo "ERROR: set your GitHub username first:"
      echo "  git config --global user.github <your-github-username>"
      exit 1
    fi
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

    # 1. Jan's CHS + scouting-UParT recipe
    run_cmd git cms-merge-topic "$DERIVED_TOPIC"

    # 2. HHbbtt production psets (baked preselection + whitelist v3)
    run_cmd git clone -b "$SCOUT_BRANCH" "$SCOUT_FORK" ScoutingNanoProduction

    run_cmd scram b -j8
    run_cmd cmsenv
    run_cmd cd "$this_dir"
    run_cmd touch "$this_dir/cmssw/$CMSSW_VER/.installed"
    echo ""
    echo "Done. Set in your .env:"
    echo "  CMSSW_AREA=$this_dir/cmssw/$CMSSW_VER"
    echo "  CMSSW_VERSION=$CMSSW_VER"
else
    run_cmd cd "$this_dir/cmssw/$CMSSW_VER/"
    run_cmd cmsenv
    run_cmd cd ../..
fi
