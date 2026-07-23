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
export SCRAM_ARCH="${SCRAM_ARCH_OVERRIDE:-el8_amd64_gcc13}"   # pre4 needs gcc13 (fresh shells may default to gcc12)

# pre4 exists only for el8. On an el9 host (e.g. lxplus default) enter the
# el8 container FIRST, then rerun this script:   cmssw-el8   (then ./setup.sh)
if grep -qE "release 9" /etc/redhat-release 2>/dev/null && [ -z "${APPTAINER_CONTAINER:-}${SINGULARITY_CONTAINER:-}" ]; then
  echo "ERROR: this is an el9 host and $CMSSW_VER is el8-only."
  echo "       Run 'cmssw-el8' to enter the el8 container, then rerun ./setup.sh"
  exit 1
fi
SCOUT_FORK="${SCOUT_FORK:-https://github.com/ArghyaRanjanDas/ScoutingNanoProduction.git}"
SCOUT_BRANCH="${SCOUT_BRANCH:-hhbbtt-chs-integration}"
# FROZEN copy of JanFSchulte:derivedScouting as validated 2026-07 (+build fix).
# Jan's live branch has moved and now CONFLICTS with the release — never point
# at it directly; the frozen branch reproduces the exact production state.
DERIVED_TOPIC="${DERIVED_TOPIC:-ArghyaRanjanDas:hhbbtt-chs-16_1_0_pre4}"

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

    # 1. The FROZEN validated recipe state (Jan's topic + conflict resolution
    #    + build fix). checkout-topic takes the resolved tree AS-IS — never
    #    use merge-topic here: pre4 already ships different PatFromScouting
    #    files, so a re-merge always conflicts.
    run_cmd git cms-checkout-topic -u "$DERIVED_TOPIC"

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
