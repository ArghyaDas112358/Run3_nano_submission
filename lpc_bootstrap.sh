#!/bin/bash
# One-shot LPC bootstrap for Run3_nano_submission (written 2026-08-17).
# Usage on any cmslpc node, from the repo root:   ./lpc_bootstrap.sh
# Re-executes itself inside the el8 container (with the /uscms_data bind the
# stock cmssw-el8 wrapper is missing), builds the CMSSW producer area via
# ./setup.sh, and interactively writes your .env.
set -e

EL8_IMAGE=/cvmfs/unpacked.cern.ch/registry.hub.docker.com/cmssw/el8:x86_64

if [ "$(grep -oP '(?<=release )\d+' /etc/redhat-release 2>/dev/null || echo 0)" != "8" ]; then
  echo "[bootstrap] not on el8 - re-launching inside the el8 container..."
  exec apptainer -s exec -B /cvmfs -B /uscms_data "$EL8_IMAGE" bash "$(readlink -f "$0")"
fi

cd "$(dirname "$(readlink -f "$0")")"
echo "[bootstrap] running in: $(pwd) (el8 container)"

if ! git config --global user.github > /dev/null 2>&1; then
  read -rp "[bootstrap] your GitHub username (needed by git cms-checkout-topic): " GH
  git config --global user.github "$GH"
fi

if [ -d cmssw/CMSSW_16_1_0_pre4/src ]; then
  echo "[bootstrap] CMSSW area already exists - skipping setup.sh"
else
  echo "[bootstrap] building the CMSSW producer area (~15-25 min)..."
  source /cvmfs/cms.cern.ch/cmsset_default.sh
  ./setup.sh
fi

if [ -f .env ]; then
  echo "[bootstrap] .env already exists - leaving it alone"
else
  echo "[bootstrap] creating your .env"
  read -rp "  CERN/grid username: " CU
  read -rp "  FNAL username: " FU
  read -rp "  Storage site [T3_US_FNALLPC]: " SS
  SS=${SS:-T3_US_FNALLPC}
  cat > .env <<ENVEOF
CERN_USER=$CU
FNAL_USER=$FU
PURDUE_USER=
CMSSW_AREA=$(pwd)/cmssw/CMSSW_16_1_0_pre4
CMSSW_VERSION=CMSSW_16_1_0_pre4
STORAGE_SITE=$SS
ENVEOF
  echo "  wrote .env:"; sed "s/^/    /" .env
fi

cat <<'NEXTEOF'

[bootstrap] DONE. Next steps (see LPC_SETUP.md for the full ritual + gotchas):
  1. crab createmyproxy --days 30          (one-time)
  2. per session, inside the container:
       set -a; source .env; set +a
       source /cvmfs/cms.cern.ch/cmsset_default.sh
       cd cmssw/$CMSSW_VERSION/src && cmsenv && cd ../../..
       source /cvmfs/cms.cern.ch/common/crab-setup.sh   # AFTER cmsenv, order matters
       voms-proxy-init --voms cms --valid 168:00
  3. SELF-TEST FIRST (never straight to a full round):
       python3 crabby.py --year 2024 --dataset TT --scouting --make --submit --test \
           --card cards/chs_mc.yml --campaign NanoAODv17ScoutingCHS24 --user $FNAL_USER
NEXTEOF
