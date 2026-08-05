"""
This script is used to submit crab jobs for Run3 nanoAOD production.
"""

#! /usr/bin/env python3
import yaml
import argparse
import os
import re
import copy
import json
from pathlib import Path

# CRAB is imported LAZILY, inside submit(), on purpose.
#
# A module-scope `from CRABAPI.RawCommand import crabCommand` made the whole
# tool unusable without a full CRAB environment — including `--make`, which
# only writes text files and needs no CRAB at all. That broke the two-phase
# `--make` -> inspect -> `--submit` workflow the docs prescribe, and greeted a
# new collaborator with a bare ModuleNotFoundError (found by the cold-start
# rehearsal, 2026-08-04). Our own shells always had crab-setup.sh sourced, so
# this was invisible from the inside.
from http.client import HTTPException


def _crab_command():
    """Import CRABAPI on demand, or explain exactly how to get it."""
    try:
        from CRABAPI.RawCommand import crabCommand
    except ImportError:
        raise SystemExit(
            "CRAB client not available (no module named 'CRABAPI').\n"
            "Only --submit and --status need it; --make works without.\n"
            "To submit, set up CRAB in this shell first:\n"
            "    source /cvmfs/cms.cern.ch/cmsset_default.sh\n"
            "    cd \"$CMSSW_AREA/src\" && cmsenv && cd -\n"
            "    source /cvmfs/cms.cern.ch/common/crab-setup.sh\n"
            "See CLAUDE.md 'Every-session setup'."
        )
    return crabCommand

# in python3, http.client replaces httplib
import string
import random
import hashlib


TAG = "25v2"

DATASETS = ["JetMET", "EGamma", "Muon", "MuonEG", "BTagMu", "Tau",
            "ParkingVBF", "ParkingSingleMuon", "ScoutingHLT",
            # per-era HLTSCOUT groups (single-era claims, RUNBOOK 4b)
            "ScoutingHLT_Run2024C", "ScoutingHLT_Run2024D", "ScoutingHLT_Run2024E",
            "ScoutingHLT_Run2024F", "ScoutingHLT_Run2024G", "ScoutingHLT_Run2024H",
            "ScoutingHLT_Run2024I"]

CONFIGS = {
    "data": {
        "2022": "DATA_2022_NANO.py",
        "2022EE": "DATA_2022_NANO.py",
        "2023": "DATA_2023_NANO.py",
        "2023BPix": "DATA_2023_NANO.py",
        "2024": "DATA_2024_NANO.py",
    },
    "mc": {
        "2022": "MC_preEE2022_NANO.py",
        "2022EE": "MC_postEE2022_NANO.py",
        "2023": "MC_preBPix2023_NANO.py",
        "2023BPix": "MC_postBPix2023_NANO.py",
        "2024": "MC_2024_NANO.py",
    },
    "mcscouting": {
        "2022": "MC_preEE2022_NANO.py",
        "2022EE": "MC_postEE2022_NANO.py",
        "2023": "MC_preBPix2023_NANO.py",
        "2023BPix": "MC_postBPix2023_NANO.py",
        "2024": "MC_2024_Scouting.py",
    },
}

JSONS = {
    "2022": "Cert_Collisions2022_355100_362760_Golden.json",
    "2022EE": "Cert_Collisions2022_355100_362760_Golden.json",
    "2023": "Cert_Collisions2023_366442_370790_Golden.json",
    "2023BPix": "Cert_Collisions2023_366442_370790_Golden.json",
    "2024": "Cert_Collisions2024_378981_386951_Golden.json",
}


def submit(config):
    try:
        _crab_command()("submit", config=config)
    except HTTPException as hte:
        print("Cannot execute command")
        print(hte.headers)


def resolve_pset(raw: str) -> str:
    """Expand the card's pset path and FAIL LOUDLY if it cannot work.

    ``os.path.expandvars`` silently keeps ``${CMSSW_AREA}`` as a literal when
    the variable is unset, so ``--make`` used to succeed and the user only hit
    CRAB's opaque "Cannot find CMSSW configuration file ${CMSSW_AREA}/..."
    at submit time (seen in the field on lxplus, 2026-08-04). Refuse here,
    with the recipe, before anything is made or submitted.
    """
    pset = os.path.expandvars(raw)
    if "$" in pset:
        raise SystemExit(
            f"pset path did not expand: {pset}\n"
            "CMSSW_AREA is not set in this shell. Fix:\n"
            "    cp .env.example .env   # once; then edit CMSSW_AREA etc.\n"
            "    set -a; source .env; set +a\n"
            "    ./setup.sh             # once, if the CMSSW area is not built yet\n"
            "then re-run this command. See README.md 'Quick start' / RUNBOOK_CHS.md."
        )
    if not os.path.isfile(pset):
        raise SystemExit(
            f"pset file does not exist: {pset}\n"
            "CMSSW_AREA points somewhere without the ScoutingNanoProduction package.\n"
            "Run ./setup.sh (builds the area and checks the package out), or fix\n"
            "CMSSW_AREA in .env to the area setup.sh created: <harness>/cmssw/<release>."
        )
    return pset


def rnd_str(N, seedstr="test"):
    # Seed with dataset name hash to be reproducible
    random.seed(int(hashlib.sha512(seedstr.encode("utf-8")).hexdigest(), 16))
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(N))


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def resolve_splitting(card, dataset):
    """``(splitting, unitsPerJob)`` for one dataset, honouring card overrides.

    CRAB's TaskWorker REFUSES a task whose input dataset has any block carrying
    more than 100,000 lumis -- looking that many up would blow up the server's
    memory -- and the only way through is a splitting mode that never consults
    lumi information at all, i.e. ``FileBased``.

    The trap is the timing: the refusal happens AFTER the client has printed
    "Success: Your task has been delivered", so ``crab.log`` is clean, the
    RUNBOOK's self-test criterion passes, and the only visible symptom is that
    no output file ever appears. ``crab status`` says ``SUBMITREFUSED``. This
    bit WtoLNu-4Jets_Bin-4J on 2026-07-25 and cost the group eleven days of
    thinking that stem was fine.

    Overrides are declared per card so the knowledge lives next to the campaign
    it belongs to rather than in code::

        splitting_overrides:
          - match: "WtoLNu-4Jets_Bin-4J"     # substring of the dataset path
            splitting: FileBased
            unitsPerJob: 1

    First matching rule wins. ``unitsPerJob`` is ``None`` when the rule does not
    set one; note that ``Automatic`` splitting rejects ``unitsPerJob`` outright,
    so a FileBased override must supply it.
    """
    default = "LumiBased" if card["data"] else "Automatic"
    for rule in card.get("splitting_overrides") or []:
        match = rule.get("match")
        if match and match in dataset:
            return rule.get("splitting", default), rule.get("unitsPerJob")
    return default, None


def make(card, datasets, base_crab_config, test: bool):
    """Make crab configs."""
    print("Making configs in {}:".format(card["workArea"]))
    for dataset in datasets:
        print("   ==> " + dataset)
        crab_config = copy.deepcopy(base_crab_config)
        dataset_name = dataset.lstrip("/").replace("/", "_")

        tag = dataset.split("/")[2]
        if card["tag_mod"] is not None:
            tag = (
                re.sub(r"MiniAOD[v]?[0-9]?", card["tag_mod"], tag)
                if tag.startswith("RunII")
                else tag + "_" + card["tag_mod"]
            )
        elif card["tag_extension"] is not None:
            tag = tag + "_" + card["tag_extension"]
        else:
            raise ValueError(
                "Either ``campaign: tag_mod`` or ``campaign: tag_extension`` need to be specified"
            )

        if len(dataset_name) < 95:
            request_name = dataset_name
        else:
            request_name = dataset_name[:90] + rnd_str(8, dataset_name)

        verbatim_lines = []
        splitting, split_units = resolve_splitting(card, dataset)
        if splitting != ("LumiBased" if card["data"] else "Automatic"):
            print("  [splitting override] {} -> {}{}".format(
                dataset.split("/")[1], splitting,
                "" if split_units is None else ", unitsPerJob = {}".format(split_units)))
        card_info = {
            "_requestName_": request_name,
            "_workArea_": card["workArea"],
            "_psetName_": resolve_pset(card["config"]),
            "_inputDataset_": dataset,
            "_outLFNDirBase_": card["outLFNDirBase"],
            "_storageSite_": card["storageSite"],
            "_publication_": str(card["publication"]),
            "_splitting_": splitting,
            "_outputDatasetTag_": tag,
        }

        if test:
            verbatim_lines.append("config.Data.totalUnits = 1")
            card_info["_publication_"] = "False"

        if split_units is not None:
            verbatim_lines.append("config.Data.unitsPerJob = {}".format(split_units))
        if card["data"]:
            # the override, when it sets unitsPerJob, wins over the data default
            if split_units is None:
                verbatim_lines.append("config.Data.unitsPerJob = 50")
            verbatim_lines.append("config.JobType.maxJobRuntimeMin = 2750")
        if card["data"] and card["lumiMask"] is not None:
            verbatim_lines.append("config.Data.lumiMask = '{}'".format(card["lumiMask"]))
        if card["voGroup"] is not None:
            verbatim_lines.append("config.User.voGroup = '{}'".format(card["voGroup"]))

        for line in verbatim_lines:
            crab_config += "\n" + line
        crab_config += "\n"

        for key in card_info:
            crab_config = crab_config.replace(key, card_info[key])

        cfg_filename = os.path.join(card["workArea"], "submit_{}.py".format(dataset_name))
        with open(cfg_filename, "w") as cfg_file:
            cfg_file.write(crab_config)


def submit_wrapper(card, datasets, base_crab_config, test: bool):
    """Submit crab configs."""
    from multiprocessing import Process
    import imp

    print("Submitting configs:")
    for dataset in datasets:
        print("   ==> " + dataset)
        dataset_name = dataset.lstrip("/").replace("/", "_")
        cfg_filename = os.path.join(card["workArea"], "submit_{}.py".format(dataset_name))
        config_file = imp.load_source("config", cfg_filename)
        p = Process(target=submit, args=(config_file.config,))
        p.start()
        p.join()


def status(card, datasets, card_name=None):
    """Get status of crab jobs."""
    das_names = []
    for dataset in datasets:
        dataset_name = dataset.lstrip("/").replace("/", "_")
        if len(dataset_name) < 95:
            request_name = dataset_name
        else:
            request_name = dataset_name[:90] + rnd_str(8, dataset_name)
        cfg_dir = os.path.join(card["workArea"], "crab_" + request_name)
        o = os.popen("crab status " + cfg_dir).read().split("\n")
        for i, line in enumerate(o):
            if line.startswith("CRAB project directory:"):
                print(line)  # in python3, print(line) replaces print line
            if line.startswith("Jobs status"):
                for j in range(5):
                    if len(o[i + j]) < 2:
                        continue
                    if any(
                        s in o[i + j]
                        for s in [
                            "unsubmitted",
                            "idle",
                            "finished",
                            "running",
                            "transferred",
                            "transferring",
                            "failed",
                        ]
                    ):
                        print(o[i + j])

            if "Output dataset:" in line:
                das_names.append(line.split()[-1])

    if card_name is None:
        # Back-compat: fall back to the legacy module-global ``args.card``.
        _args = globals().get("args")
        card_name = getattr(_args, "card", None) if _args is not None else None
    if card_name:
        stem = card_name.split("/")[-1].split(".")[0]
    else:
        stem = card.get("name", "status")
    das_names_file = "outputs_{}.txt".format(stem)
    print("Writing output dataset DAS names to: {}".format(das_names_file))
    with open(das_names_file, "w") as das_file:
        das_file.write("\n".join(das_names))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", required=False, default="", type=str, help="username for storing files")
    parser.add_argument(
        "--year",
        required=True,
        type=str,
        choices=["2022", "2022EE", "2023", "2023BPix", "2024"],
        help="year",
    )
    parser.add_argument(
        "--dataset", required=True, type=str, help="dataset to submit, e.g. JetMET, HH4b, etc."
    )
    parser.add_argument(
        "--card", default=None, type=str, help="(Optional) path to the crab config file"
    )
    parser.add_argument(
        "--make", action="store_true", help="Make crab configs according to the spec."
    )
    parser.add_argument(
        "--submit", action="store_true", help="Submit configs created by ``--make``."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Run `crab submit` but filter for only status info. Creates a list of DAS names.",
    )
    parser.add_argument(
        "--test",
        type=str2bool,
        default="False",
        choices={True, False},
        help="Test submit - only 1 file, don't publish.",
    )
    parser.add_argument(
        "--scouting", default=False, action="store_true", help="Produce scouting samples"
    )
    # Canonical spelling; --campain kept as a deprecated alias (see below).
    parser.add_argument(
        "--campaign",
        dest="campaign",
        required=False,
        default="NanoAODv15Scouting24",
        type=str,
        help="Production campaign tag (used in workArea + outLFNDirBase).",
    )
    parser.add_argument(
        "--campain",
        dest="campaign",
        required=False,
        default=argparse.SUPPRESS,
        type=str,
        help=argparse.SUPPRESS,  # hidden — deprecated typo of --campaign
    )
    args = parser.parse_args()

    # Deprecation warning if the user typed --campain (the typo).
    import sys
    if "--campain" in sys.argv:
        print(
            "WARNING: --campain is a deprecated typo of --campaign; please update "
            "your scripts.  Both flags currently set the same value.",
            file=sys.stderr,
        )

    if (args.user == ""):
        args.user = os.environ['USER'].split("-")[0]

    if (args.campaign != ""):
        global TAG
        TAG = args.campaign

    return args


def main(args):
    if args.card is not None:
        with open(args.card, "r") as f:
            input_card = yaml.safe_load(f)

        if "campaign" in input_card:
            input_card = input_card["campaign"]
    else:
        input_card = {}

    isData = args.dataset in DATASETS
    dlabel = "data" if isData else "mc"
    if args.scouting:
        dlabel = "datascouting" if isData else "mcscouting"
        # Only 2024 has a distinct scouting pset; earlier years map to the
        # same non-scouting config (see CONFIGS).  Warn so users don't think
        # they got scouting output when they didn't.
        if args.year != "2024" and CONFIGS.get(dlabel, {}).get(args.year) == CONFIGS["mc"].get(args.year):
            import sys
            print(
                f"WARNING: --scouting has no effect for year {args.year}: "
                f"the {dlabel} config for {args.year} is identical to the non-scouting "
                f"config ({CONFIGS[dlabel].get(args.year, '<missing>')}). Only 2024 ships "
                f"a dedicated scouting pset (MC_2024_Scouting.py). "
                f"crab/{TAG}/{dlabel}_{args.year}_… work area names will still use the "
                f"'{dlabel}' prefix, but the output will be standard NanoAOD.",
                file=sys.stderr,
            )
    # mc_campaign = MC_CAMPAIGNS[args.year]
    # miniaod_version = "MINIAODv4"
    if isData:
        jsonFile = f"datasets/DATA_{args.year}.json"
    else:
        jsonFile = f"datasets/MC_{args.year}.json"
    with Path(jsonFile).open("r") as f:
        datasets = json.load(f)[args.dataset]

    defaults = {
        "name": f"{dlabel}_{args.year}_{args.dataset}",
        "crab_template": "template_crab.py",
        "workArea": f"crab/{TAG}/{dlabel}_{args.year}_{args.dataset}",
        "storageSite": os.environ.get("STORAGE_SITE", "T2_US_Purdue"),
        "outLFNDirBase": f"/store/user/{args.user}/production/Scouting/{args.campaign}/{dlabel}_{args.year}",
        "voGroup": None,
        "publication": True,
        # No repo-shipped config exists for some dlabels (e.g. datascouting —
        # the CHS data pset lives in the CMSSW area, supplied via the card).
        "config": (f"configs/{CONFIGS[dlabel][args.year]}"
                   if CONFIGS.get(dlabel, {}).get(args.year) else None),
        "tag_extension": "DAZSLE_PFNano",
        "tag_mod": None,
        "data": isData,
        "lumiMask": f"jsons/{JSONS[args.year]}" if isData else None,
        # per-dataset splitting rules; see resolve_splitting()
        "splitting_overrides": [],
        "datasets": datasets,
    }

    card = defaults | input_card

    if not card["config"]:
        exit(f"ERROR: no cmsRun config for '{dlabel}/{args.year}'. "
             f"This category needs a card that provides one, e.g. "
             f"--card cards/chs_data.yml (see RUNBOOK_CHS.md 4b).")

    work_area = Path(card["workArea"])
    if work_area.exists():
        if args.submit or args.make:
            # in python3, input replaces raw_input
            if input(f"``workArea: {work_area}`` already exists. Continue? (y/n)") != "y":
                exit()
    else:
        work_area.mkdir(parents=True, exist_ok=True)

    if (card["tag_mod"] is not None) and (card["tag_extension"] is not None):
        print(
            "Can't specify both ``campaign: tag_mod`` and ``campaign: tag_extension``. Leave one empty."
        )
        exit()

    with open(card["crab_template"], "r") as template_file:
        base_crab_config = template_file.read()

    datasets = [value for key, value in card["datasets"].items() if len(value) > 10 and not value.startswith("#")]

    if args.make:
        make(card, datasets, base_crab_config, args.test)

    if args.submit:
        submit_wrapper(card, datasets, base_crab_config, args.test)

    if args.status:
        status(card, datasets, args.card)


if __name__ == "__main__":
    args = parse_args()
    main(args)
