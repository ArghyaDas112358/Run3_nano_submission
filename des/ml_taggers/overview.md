# ML Jet Taggers: Overview and Comparison

## Purpose

The Scouting NanoAOD production pipeline deploys multiple machine-learning jet taggers
to classify jets by their originating parton flavor. For the HH->bb(tautau) analysis,
discriminating b-jets, tau-jets, and light-flavor jets is critical. This document
summarizes all taggers used in the pipeline, how they relate to one another, and where
their outputs appear in the final NanoAOD files.

## Tagger Summary Table

| Tagger | Jet Collection | Cone Size | Architecture | Num Outputs | Execution Level | Model Path |
|--------|---------------|-----------|--------------|-------------|----------------|------------|
| UParT AK4 (Scouting) | Reclustered AK4 | R=0.4 | Unified Particle Transformer | 8 | Reco-level (offline on scouting data) | `UParTAK4/Scouting_HHbbtautau/V00/` |
| HLT ParticleNet AK4 | Reclustered AK4 | R=0.4 | Dynamic Graph CNN (ParticleNet) | 7 | Re-run at reco level using HLT-style features | `HLT/ParticleNetAK4/V01/` |
| HLT ParticleNet AK8 | Reclustered AK8 | R=0.8 | Dynamic Graph CNN (ParticleNet) | 10 | Re-run at reco level using HLT-style features | `HLT/ParticleNetAK8/V01/` |
| GloParT AK8 | Standard AK8 | R=0.8 | Global Particle Transformer | 22+ | Reco-level (standard CMSSW) | `GlobalParticleTransformerAK8/PUPPI/V03/` |

## Output Discriminant Details

### UParT AK4 (Scouting_HHbbtautau)

Produces 8 flavor probability scores per reclustered AK4 jet:

| Output | NanoAOD Branch | Description |
|--------|---------------|-------------|
| `probb` | `ScoutingPFJetRecluster2_scoutUParT_probb` | b quark probability |
| `probbb` | `ScoutingPFJetRecluster2_scoutUParT_probbb` | bb (merged b-pair) probability |
| `problepb` | `ScoutingPFJetRecluster2_scoutUParT_problepb` | Leptonic b decay probability |
| `probc` | `ScoutingPFJetRecluster2_scoutUParT_probc` | c quark probability |
| `probuds` | `ScoutingPFJetRecluster2_scoutUParT_probuds` | Light quark (u, d, s) probability |
| `probg` | `ScoutingPFJetRecluster2_scoutUParT_probg` | Gluon probability |
| `probtaum` | `ScoutingPFJetRecluster2_scoutUParT_probtaum` | Tau-minus probability |
| `probtaup` | `ScoutingPFJetRecluster2_scoutUParT_probtaup` | Tau-plus probability |

Selection: pT >= 15 GeV and |eta| <= 2.5. Scores set to -1 outside acceptance.

### HLT ParticleNet AK4

Produces 7 scores per reclustered AK4 jet:

| Output | NanoAOD Branch | Description |
|--------|---------------|-------------|
| `probtauhp` | `ScoutingPFJetRecluster2_hltPNet_probtauhp` | Hadronic tau (positive) probability |
| `probtauhm` | `ScoutingPFJetRecluster2_hltPNet_probtauhm` | Hadronic tau (negative) probability |
| `probb` | `ScoutingPFJetRecluster2_hltPNet_probb` | b quark probability |
| `probc` | `ScoutingPFJetRecluster2_hltPNet_probc` | c quark probability |
| `probuds` | `ScoutingPFJetRecluster2_hltPNet_probuds` | Light quark probability |
| `probg` | `ScoutingPFJetRecluster2_hltPNet_probg` | Gluon probability |
| `ptcorr` | (not stored in NanoAOD) | pT correction factor |

Selection: pT >= 5 GeV and |eta| <= 2.6. Scores set to -1 outside acceptance.

### HLT ParticleNet AK8

Produces 10 scores per reclustered AK8 fat jet:

| Output | NanoAOD Branch | Description |
|--------|---------------|-------------|
| `probHtt` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHtt` | H -> tau_h tau_h |
| `probHtm` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHtm` | H -> tau_h tau_mu |
| `probHte` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHte` | H -> tau_h tau_e |
| `probHbb` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHbb` | H -> bb |
| `probHcc` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHcc` | H -> cc |
| `probHqq` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHqq` | H -> qq (light) |
| `probHgg` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHgg` | H -> gg |
| `probQCD2hf` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD2hf` | QCD with 2 heavy-flavor |
| `probQCD1hf` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD1hf` | QCD with 1 heavy-flavor |
| `probQCD0hf` | `ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD0hf` | QCD with 0 heavy-flavor |

Selection: pT >= 200 GeV and |eta| <= 2.5. Scores set to -1 outside acceptance.

## Execution Level: Reco vs HLT

None of the taggers in this pipeline reuse pre-computed HLT scores directly from
data-taking. Instead, all taggers are re-run at reconstruction level on translated
scouting objects:

1. **Scouting data** arrives as packed HLT objects (`hltScoutingPFPacker`, etc.).
2. **ScoutingTranslator** converts them to standard reco format (PFCandidates, Tracks, Vertices).
3. **Jets are reclustered** from the translated PF candidates (AK4 at pT > 20 GeV, AK8 at pT > 170 GeV).
4. **TagInfo producers** extract features from the reclustered jets and their constituents.
5. **ONNX inference** runs the neural network models to produce discriminant scores.

The HLT ParticleNet taggers use `use_hlt_features = True`, meaning they extract features
in the HLT-compatible format (reduced feature set). The UParT tagger uses a dedicated
scouting feature extractor that accounts for missing lost tracks and PUPPI weights.

## Dual Tagging Strategy for AK4 Jets

Reclustered AK4 jets carry scores from both HLT ParticleNet and UParT taggers. This
serves complementary purposes:

- **HLT ParticleNet**: Operates at lower pT threshold (5 GeV), provides tau discrimination
  via `probtauhp`/`probtauhm` categories, and offers a baseline b-tag reference that mirrors
  online trigger decisions.

- **UParT (Scouting_HHbbtautau)**: Higher-quality offline tagger with 8 outputs including
  dedicated `probtaum`/`probtaup` classes for tau-jet identification. Specifically trained
  on scouting-format data for the HH->bb(tautau) signal topology.

## Combining Tagger Outputs for Analysis

For the HH->bb(tautau) search, typical discriminant combinations include:

- **b-tagging**: Use `scoutUParT_probb + scoutUParT_probbb + scoutUParT_problepb` as a
  combined b-jet score, or individual components for fine-grained working points.

- **Tau-jet identification**: Use `scoutUParT_probtaum + scoutUParT_probtaup` to select
  hadronic tau candidates, with the charge-split categories allowing charge-bias studies.

- **Light-flavor rejection**: The `probuds` and `probg` scores enable vetoing QCD jets.

- **Cross-validation**: Compare UParT and HLT PNet b-scores to assess tagger agreement
  and derive systematic uncertainties.

- **Boosted H->tautau**: Use HLT PNet AK8 `probHtt + probHtm + probHte` to tag
  merged Higgs decays in the high-pT regime.

## GloParT AK8 in Standard CMSSW

The Global Particle Transformer for AK8 jets (GloParT AK8) is available in the standard
CMSSW infrastructure but is **not currently integrated** into the scouting NanoAOD pipeline.
It is referenced here for completeness, as it could be added in a future iteration
to complement the HLT ParticleNet AK8 scores on fat jets. See `glopart_ak8.md` for details
on its architecture and outputs.
