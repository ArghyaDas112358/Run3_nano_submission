#!/bin/bash

NEVENTS=10
NTHREADS=4
ERA=Run3_2024

############# Common arguments #############

base_args=(
  --customise DAZSLE/DAZSLE/customize.customize
  --step NANO:@BTV
  --scenario pp
  --customise_commands "process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000"
  --no_exec
  -n $NEVENTS
  --nThreads $NTHREADS
  --era $ERA
)

mc_args=(
  --eventcontent NANOAODSIM
  --datatier NANOAODSIM
  --mc
)

data_args=(
  --eventcontent NANOAOD
  --datatier NANOAOD
  --data
)

############# Scouting arguments #############

scouting_args=(
  -s NANO:@GENFromMini+@ScoutFromMini
  --process NANO
  -n $NEVENTS
  --nThreads $NTHREADS
  --era $ERA
  --customise PhysicsTools/NanoAOD/custom_run3scouting_cff.addScoutingPFCandidate
  --customise_commands "process.NANOAODSIMoutput.outputCommands.append(\"keep edmTriggerResults_*_*_*\")"
  --no_exec
)

############# Example: Scouting MC #############

name=MC_2024_Scouting
gt=auto:phase1_2024_realistic
filein=/store/mc/RunIII2024Summer24MiniAODv6/GluGluHHto2B2Tau_Par-c2-0p00-kl-0p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/MINIAODSIM/PowhegBugFix_150X_mcRun3_2024_realistic_v2-v2/2520000/02adb734-559d-4c0e-997d-984f4ef0f62e.root

cmsDriver.py \
  --python_filename ${name}.py \
  "${scouting_args[@]}" \
  "${mc_args[@]}" \
  --fileout file:${name}.root \
  --conditions $gt \
  --filein $filein
