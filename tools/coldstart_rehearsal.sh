#!/bin/bash
# COLD-START REHEARSAL — the collaborator path, verbatim from the docs, in a
# fresh directory. Every step a new user runs, run here; every failure Marc
# hit, asserted against. Writes PASS/FAIL per step; exit 0 only if ALL pass.
set -u
R=/tmp/claude-978920/-work-users-das214-analysis-scouting-HHbbtautau/7ea87f19-a0b2-45be-ab42-455d87988ccf/scratchpad/coldstart
LOG=$R/steps.log
rm -rf $R && mkdir -p $R && cd $R
fail=0
step() { echo "── STEP: $1" | tee -a $LOG; }
check() { if eval "$2"; then echo "PASS: $1" | tee -a $LOG; else echo "FAIL: $1" | tee -a $LOG; fail=1; fi; }

step "clone from GitHub (what Marc pulls, incl. today's fixes)"
git clone -q -b NanoAODv17_CHS https://github.com/ArghyaRanjanDas/Run3_nano_submission repo >> $LOG 2>&1
check "clone" "[ -f repo/setup.sh ]"
cd repo

step ".env from template, exactly per README"
cp .env.example .env
sed -i "s|^CMSSW_AREA=.*|CMSSW_AREA=$R/repo/cmssw/CMSSW_16_1_0_pre4|" .env
sed -i "s|^PURDUE_USER=.*|PURDUE_USER=coldstart|; s|^CERN_USER=.*|CERN_USER=coldstart|; s|^FNAL_USER=.*|FNAL_USER=coldstart|" .env
set -a; source .env; set +a
check "CMSSW_AREA exported to python" "python3 -c 'import os,sys; sys.exit(0 if os.environ.get(\"CMSSW_AREA\") else 1)'"

step "setup.sh (full CMSSW build — the long pole)"
./setup.sh >> $LOG 2>&1
check "setup.sh exit 0" "[ $? -eq 0 ] && [ -f cmssw/CMSSW_16_1_0_pre4/.installed ]"
check "pset exists (Marc failure #1 class)" "[ -f \$CMSSW_AREA/src/ScoutingNanoProduction/scoutingnano_data_hhbbtt.py ]"
check "presel filter plugin installed (Marc failure #3)" "[ -f \$CMSSW_AREA/src/PhysicsTools/PatFromScouting/plugins/HHbbttPreselFilter.cc ]"
check "ONNX models installed (Marc failure #2)" "[ -f \$CMSSW_AREA/src/RecoBTag/CombinedScouting/data/model_v3.onnx ] && [ -f \$CMSSW_AREA/src/RecoBTag/CombinedScouting/data/model_upartv2.onnx ] && [ -f \$CMSSW_AREA/src/RecoBTag/CombinedScouting/data/model_tautagging.onnx ]"

step "pytest suite in the fresh clone"
python3 -m pytest tests -q >> $LOG 2>&1
check "pytest green" "[ $? -eq 0 ]"

step "--make with NO CRAB environment (Marc failure #4)"
check "crabby imports without CRABAPI" "python3 -c 'import sys; sys.path.insert(0,\".\"); import crabby' 2>/dev/null"

step "every-session shell per CLAUDE.md, then --make MC and DATA (no submit)"
( set -a; source .env; set +a
  cd "$CMSSW_AREA/src"; source /cvmfs/cms.cern.ch/cmsset_default.sh; eval $(scramv1 runtime -sh)
  source /cvmfs/cms.cern.ch/common/crab-setup.sh 2>/dev/null; cd $R/repo
  python3 crabby.py --year 2024 --dataset HHbbtt --scouting --make --campaign NanoAODv17ScoutingCHS24 --user coldstart >> $LOG 2>&1 || echo MC_MAKE_RC=$? >> $LOG
  python3 crabby.py --year 2024 --dataset ScoutingHLT_Run2024D --scouting --card cards/chs_data.yml --make --campaign NanoAODv17ScoutingCHS24 --user coldstart >> $LOG 2>&1 || echo DATA_MAKE_RC=$? >> $LOG )
check "MC configs generated" "ls crab/NanoAODv17ScoutingCHS24/mcscouting_2024_HHbbtt/*.py >/dev/null 2>&1"
check "DATA configs generated" "ls crab/NanoAODv17ScoutingCHS24/datascouting_2024_ScoutingHLT_Run2024D/*.py >/dev/null 2>&1"
check "at least one config exists (guards the checks below)" "[ \$(ls crab/*/*/*.py 2>/dev/null | wc -l) -gt 0 ]"
check "no unexpanded \$ in ANY generated config (Marc failure #1)" "! grep -rl 'CMSSW_AREA' crab/ 2>/dev/null | grep -q ."
check "psetName in generated configs points at a real file" "python3 -c \"
import glob,re,sys
bad=[]
for f in glob.glob('crab/**/*.py',recursive=True):
    m=re.search(r'psetName = .([^\\\"\\x27]+)', open(f).read())
    if m:
        import os
        if not os.path.isfile(m.group(1)): bad.append((f,m.group(1)))
sys.exit(1 if bad else 0)\""

echo "──────────────"; echo "COLDSTART RESULT: $([ $fail -eq 0 ] && echo ALL PASS || echo FAILURES PRESENT)" | tee -a $LOG
exit $fail
