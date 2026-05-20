# Design Documentation: HH→bbττ Scouting NanoAOD

Comprehensive design documentation for the `Run3_nano_submission` repository, which produces Scouting NanoAOD with advanced ML jet taggers (UParT, GloParT, HLT ParticleNet) for the HH→bbττ analysis at CMS.

**CMSSW Version:** `CMSSW_16_0_1`
**NanoAOD Version:** NanoAODv15
**Branch:** `NanoAODv15_151_Scouting_PAF`

---

## Architecture

High-level system design, data flow, and CMSSW build integration.

- [System Architecture Overview](architecture/overview.md) — Pipeline diagram, CMSSW packages, processing modes
- [Data Flow](architecture/data_flow.md) — HLT Scouting → Translation → Reclustering → Tagging → NanoAOD
- [CMSSW Integration](architecture/cmssw_integration.md) — Build process, external packages, branch strategy

## Scouting Translator

The `PhysicsTools/ScoutingTranslator` package that converts HLT packed formats to reco objects.

- [Package Overview](scouting_translator/overview.md) — Purpose, structure, producer inventory
- [Translation Layer](scouting_translator/translation_layer.md) — HLT packed → reco conversion, PDG mapping, ValueMaps
- [AK4 Reclustering](scouting_translator/ak4_reclustering.md) — 9-step AK4 jet pipeline with UParT integration
- [AK8 Reclustering](scouting_translator/ak8_reclustering.md) — AK8 fat jet pipeline, HLT ParticleNet AK8
- [Vertex Reconstruction](scouting_translator/vertices.md) — Primary & secondary vertices, IVF, track association

## ML Jet Taggers

Machine learning taggers for jet flavor classification.

- [Tagger Overview](ml_taggers/overview.md) — Comparison table of all taggers
- [UParT AK4](ml_taggers/upart_ak4.md) — Unified Particle Transformer: architecture, 6 tensor inputs, 8 outputs
- [ONNX Inference](ml_taggers/onnx_inference.md) — Runtime model loading, batching, feature extraction
- [HLT ParticleNet](ml_taggers/hlt_particlenet.md) — ParticleNet AK4 (7 outputs) & AK8 (10 outputs)
- [GloParT AK8](ml_taggers/glopart_ak8.md) — Global Particle Transformer: 17 flavors + mass regression
- [Model Files](ml_taggers/models.md) — Scouting vs Scouting_HHbbtautau variants, versioning

## NanoAOD Output

Output file structure and branch documentation.

- [Output Overview](nanoaod_output/overview.md) — File structure, collection summary, scouting vs standard
- [Jet Branches](nanoaod_output/jet_branches.md) — AK4 & AK8 kinematics + all tagger score branches
- [Scouting Collections](nanoaod_output/scouting_collections.md) — PF candidates, leptons, photons, MET, vertices
- [Generator Collections](nanoaod_output/gen_collections.md) — GenPart, GenJet, weights, tau lifetime variables
- [Triggers](nanoaod_output/triggers.md) — Scouting & standard trigger paths, TrigObj, L1

## Configuration

CMSSW config files and customization layers.

- [Config Overview](configs/overview.md) — Comparison matrix across all config files
- [Scouting Config](configs/scouting_config.md) — `MC_2024_Scouting.py` deep dive
- [Standard Configs](configs/standard_configs.md) — Non-scouting MC & Data configs by year
- [Global Tags](configs/global_tags.md) — GlobalTag mapping (MC/Data × year)
- [Customizations](configs/customizations.md) — `customize.py` & `addVars.py` extensions

## Datasets

Dataset catalog and organization.

- [Dataset Overview](datasets/overview.md) — Catalog summary, naming conventions, JSON files
- [MC Samples](datasets/mc_samples.md) — HH signals, QCD, top, Higgs, DY, diboson
- [Data Samples](datasets/data_samples.md) — JetMET, Muon, EGamma, Tau, Parking streams
- [Scouting Data](datasets/scouting_data.md) — ScoutingPFRun3 datasets by year

## CRAB Submission

Grid job submission and monitoring workflow.

- [Submission Overview](submission/overview.md) — End-to-end workflow, prerequisites, quick-start
- [crabby.py](submission/crabby.md) — Dataset→config mapping, TAG versioning, batch submission
- [CRAB Template](submission/crab_template.md) — `template_crab.py`: memory, cores, splitting, storage
- [Monitoring](submission/monitoring.md) — `crab_status.py`: job tracking, resubmission, troubleshooting
