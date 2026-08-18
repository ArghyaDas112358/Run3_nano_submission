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
# Prerequisites: none. Runs natively on el8 AND el9 hosts (no container), and
# never touches your personal cmssw fork.
#
# Usage:  ./setup.sh          # first run builds (~15-25 min), later runs just cmsenv
#############################################################

CMSSW_VER="${CMSSW_VERSION:-CMSSW_16_1_0_pre4}"

_this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
_this_dir="$( cd "$( dirname "$_this_file" )" && pwd )"
_existing_arch="$(ls "$_this_dir/cmssw/$CMSSW_VER/.SCRAM" 2>/dev/null | grep -m1 -E '^el[0-9]+_')"

# pre4 ships BOTH el8 and el9 builds (same gcc13), so a fresh build just matches
# the host and NO container is needed anywhere (el9 nodes included). Fresh shells
# may default to gcc12 -> always set it explicitly.
# An area that already exists keeps the arch it was BUILT with: re-running this
# from a different host must never cmsenv an el8 area with an el9 arch.
if [ -n "${SCRAM_ARCH_OVERRIDE:-}" ]; then
  export SCRAM_ARCH="$SCRAM_ARCH_OVERRIDE"
elif [ -n "$_existing_arch" ]; then
  export SCRAM_ARCH="$_existing_arch"
elif grep -qE "release 9" /etc/redhat-release 2>/dev/null; then
  export SCRAM_ARCH="el9_amd64_gcc13"
else
  export SCRAM_ARCH="el8_amd64_gcc13"
fi
echo "SCRAM_ARCH=$SCRAM_ARCH  ($CMSSW_VER)"
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
      echo "note: user.github is unset — fine, the checkout below is upstream-only."
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
    run_cmd eval `scramv1 runtime -sh </dev/null`

    # 0. Initialise the git area OURSELVES, upstream-only. git cms-checkout-topic
    #    would otherwise call `git cms-init` with no options (the --upstream-only
    #    default is set for cms-merge-topic ONLY), which registers your personal
    #    cmssw fork as remote `my-cmssw` and fetches every branch it has —
    #    thousands of refs nobody needs here.
    run_cmd git cms-init --upstream-only

    # 1. The FROZEN validated recipe state (Jan's topic + conflict resolution
    #    + build fix). checkout-topic takes the resolved tree AS-IS — never
    #    use merge-topic here: pre4 already ships different PatFromScouting
    #    files, so a re-merge always conflicts.
    run_cmd git cms-checkout-topic -u "$DERIVED_TOPIC"

    # 2. HHbbtt production psets (baked preselection + whitelist v3)
    run_cmd git clone -b "$SCOUT_BRANCH" "$SCOUT_FORK" ScoutingNanoProduction

    # 3. Payloads the fork README told humans to install by hand. Both were
    #    done manually during bring-up, so OUR area worked and every FRESH
    #    build was broken — the exact class of bug only a second user finds.
    #
    #    3a. ONNX taggers. Producers resolve them via edm::FileInPath under
    #        RecoBTag/CombinedScouting/data/, and a CRAB worker only receives
    #        what the sandbox ships from src/*/data/. Missing => every remote
    #        job dies with FileInPathError (hit on lxplus 2026-08-04).
    run_cmd mkdir -p RecoBTag/CombinedScouting/data
    run_cmd cp ScoutingNanoProduction/model*.onnx RecoBTag/CombinedScouting/data/

    #    3b. The preselection EDFilter. The psets do
    #        cms.EDFilter("HHbbttPreselFilter", ...), but the .cc ships in the
    #        FORK under plugins-patch/ and must be compiled INTO the topic
    #        area. The fork README claims it is "already applied in the topic
    #        area" — VERIFIED FALSE against a clean checkout of the frozen
    #        topic (2026-08-04), so install it here. BuildFile.xml in the
    #        frozen topic already carries the required <use> lines (checked
    #        against plugins-patch/BuildFile.xml.reference); assert that
    #        rather than assume it.
    run_cmd cp ScoutingNanoProduction/plugins-patch/HHbbttPreselFilter.cc \
               PhysicsTools/PatFromScouting/plugins/
    for dep in DataFormats/PatCandidates DataFormats/Common DataFormats/Scouting; do
      if ! grep -q "<use name=\"$dep\"/>" PhysicsTools/PatFromScouting/plugins/BuildFile.xml; then
        echo "ERROR: BuildFile.xml is missing <use name=\"$dep\"/> — the filter will not link."
        echo "       Compare with ScoutingNanoProduction/plugins-patch/BuildFile.xml.reference"
        exit 1
      fi
    done

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
    # Heal areas built before the payload steps existed. Both failures are
    # REMOTE-ONLY (the local area looks fine), so heal silently-correctly and
    # rebuild only when the filter had to be added.
    healed_needs_build=0
    if [ -d "src/ScoutingNanoProduction" ]; then
      if [ ! -f "src/RecoBTag/CombinedScouting/data/model_v3.onnx" ]; then
        echo "Installing ONNX payloads into RecoBTag/CombinedScouting/data/ (were missing)..."
        run_cmd mkdir -p src/RecoBTag/CombinedScouting/data
        run_cmd cp src/ScoutingNanoProduction/model*.onnx src/RecoBTag/CombinedScouting/data/
      fi
      if [ ! -f "src/PhysicsTools/PatFromScouting/plugins/HHbbttPreselFilter.cc" ]; then
        echo "Installing HHbbttPreselFilter.cc into the topic area (was missing)..."
        run_cmd cp src/ScoutingNanoProduction/plugins-patch/HHbbttPreselFilter.cc \
                   src/PhysicsTools/PatFromScouting/plugins/
        healed_needs_build=1
      fi
    fi
    if [ "$healed_needs_build" = "1" ]; then
      echo "Rebuilding to compile the newly installed filter plugin..."
      run_cmd cd src && run_cmd scram b -j8 && run_cmd cd ..
    fi
    run_cmd cd ../..
fi
