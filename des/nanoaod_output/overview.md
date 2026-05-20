# NanoAOD Output Overview

This document summarizes the structure and content of the scouting NanoAOD files
produced by the `MC_2024_Scouting.py` configuration. The output format is CMS
NanoAOD (NANOAODSIM for MC, NANOAOD for data), a flat ROOT TTree optimized for
analysis-level access.

---

## File Structure

Each output ROOT file contains three TTrees:

| TTree | Description |
|-------|-------------|
| `Events` | Per-event physics data: jets, leptons, MET, triggers, gen-level (MC) |
| `Runs` | Per-run metadata: luminosity summaries, generator cross-sections (MC), run numbers |
| `LuminosityBlocks` | Per-luminosity-block metadata: lumi section numbers, integrated luminosity |

The `Events` tree is the primary analysis tree. Each row corresponds to one
collision event. Branches are organized as flat arrays, where variable-length
collections (e.g., jets) use a counter branch (`nScoutingPFJetRecluster2`) and
per-element branches indexed from 0 to n-1.

### Compression

The output module uses LZMA compression at level 9 for maximum compression
ratio, as configured in `MC_2024_Scouting.py`:

```python
process.NANOAODSIMoutput = cms.OutputModule("NanoAODOutputModule",
    compressionAlgorithm = cms.untracked.string('LZMA'),
    compressionLevel = cms.untracked.int32(9),
)
```

---

## Output Collections Summary (Scouting Mode)

The scouting NanoAOD contains collections from two independent sequences that
run in the same job:

1. **`nanogenSequence`** (nanoAOD_step0) -- generator-level collections (MC only)
2. **`scoutingNanoSequence`** (nanoAOD_step1) -- scouting reco-level collections

### Scouting-Specific Collections

These collections are produced by the ScoutingTranslator framework
(`addAll()` from `ScoutingNanoCustomisation_cff.py`):

| Collection | Source | Description |
|------------|--------|-------------|
| `ScoutingPFJetRecluster2` | `patScoutingPFJetRecluster` | Reclustered AK4 jets with UParT + HLT PNet scores |
| `ScoutingFatPFJetRecluster2` | `patScoutingFatPFJetRecluster` | Reclustered AK8 fat jets with HLT PNet AK8 scores |
| `ScoutingPFJet2` | `patScoutingPFJet` | Direct scouting AK4 jets (from HLT packer, no reclustering) |
| `ScoutingPV` | `scoutingVerticesPF` | Primary vertices from scouting tracks |
| `ScoutingSV` | `scoutingDeepInclusiveMergedVerticesPF` | Secondary vertices (deep inclusive merging) |
| `ScoutingKshort` | `scoutingV0Candidates:Kshort` | K-short V0 candidates |
| `ScoutingLambda` | `scoutingV0Candidates:Lambda` | Lambda V0 candidates |
| `OnlineBeamSpot` | `onlineBeamSpot` | Online reconstructed beam spot position |

### Standard Scouting Collections (from `custom_run3scouting_cff`)

These collections are produced by the standard CMSSW scouting NanoAOD
customization, called before `addAll()`:

| Collection | Description |
|------------|-------------|
| `ScoutingMuon` | HLT scouting muons (NoVtx and Vtx variants merged) |
| `ScoutingElectron` | HLT scouting electrons |
| `ScoutingPhoton` | HLT scouting photons |
| `ScoutingMET` | Scouting missing transverse energy |
| `ScoutingRho` | Scouting energy density |
| `ScoutingParticle` | Raw scouting PF particles |
| `ScoutingPrimaryVertex` | HLT-level primary vertices (before offline refit) |
| `ScoutingPFJet` | Original scouting PF jets from HLT |
| `ScoutingPFJetRecluster` | Standard reclustered jets with ParticleNet scores |
| `ScoutingFatPFJetRecluster` | Standard AK8 with GloParT and HLT PNet |
| `ScoutingPFCandidate` | Translated reco::PFCandidate for downstream use |

### Generator-Level Collections (MC Only)

| Collection | Description |
|------------|-------------|
| `GenPart` | Generator-level particles |
| `GenJet` | Generator-level AK4 jets |
| `GenJetAK8` | Generator-level AK8 jets |
| `GenVtx` | Generator vertex |
| `Pileup` | Pileup information |
| `GenWeight` | Generator event weight |
| `LHEWeight` | LHE-level weights |

---

## How Scouting NanoAOD Differs from Standard NanoAOD

Standard NanoAOD (`NANO:@BTV` step with `nano_cff`) uses fully reconstructed
offline objects (PAT jets, PAT muons, etc.) from MiniAOD. Scouting NanoAOD
differs in several fundamental ways:

| Aspect | Standard NanoAOD | Scouting NanoAOD |
|--------|-----------------|------------------|
| Input objects | Offline-reconstructed PAT | HLT-level scouting packed objects |
| Jet clustering | Uses offline PF candidates | Reclusters from translated scouting PF |
| JEC payload | AK4PFPuppi / AK4PFCHS | AK4PFHLT / AK8PFHLT |
| B-tagging | DeepJet, ParticleNet, RobustParTAK4 | UParT (custom), HLT ParticleNet |
| Tau reconstruction | Full pat::Tau with DeepTau | No dedicated tau reco (jet-level tau scores) |
| MET | PuppiMET with Type-I corrections | Scouting-level MET (uncorrected) |
| Lepton ID | Full offline ID, isolation, MVA | HLT-level scouting ID variables |
| PV reconstruction | Offline adaptive vertex fitter | Re-fitted from scouting tracks |
| SV reconstruction | Offline inclusive vertex finder | Scouting-specific deep inclusive finder |
| PUPPI weights | Full PUPPI algorithm | Fallback weight = 1.0 |
| Trigger info | Full HLT menu results | Scouting trigger results only |
| PF candidates | Optional (packedPFCandidates) | Translated scouting PF candidates |

### Collections Absent in Scouting Mode

The following standard NanoAOD collections are **not present** in scouting-only
mode:

- `Jet` (standard offline AK4 jets)
- `FatJet` (standard offline AK8 jets)
- `Tau` (offline reconstructed taus)
- `Muon` (offline PAT muons -- replaced by `ScoutingMuon`)
- `Electron` (offline PAT electrons -- replaced by `ScoutingElectron`)
- `Photon` (offline PAT photons -- replaced by `ScoutingPhoton`)
- `MET` / `PuppiMET` (replaced by `ScoutingMET`)
- `SoftActivityJet` (no soft activity in scouting)
- `SubJet` (no subjet collections)
- `SV` (replaced by `ScoutingSV`)

---

## File Size Considerations

Scouting NanoAOD files tend to be moderately sized due to the inclusion of
multiple jet collections with numerous tagger score branches. Approximate sizes
per event for MC:

| Component | Approx. Size/Event |
|-----------|-------------------|
| ScoutingPFJetRecluster2 (AK4 + 14 tagger scores) | ~1-2 KB |
| ScoutingFatPFJetRecluster2 (AK8 + 10 tagger scores) | ~0.3-0.5 KB |
| ScoutingPFJet2 (direct jets) | ~0.5-1 KB |
| Scouting leptons, MET, PV/SV | ~0.5-1 KB |
| Generator-level (MC only) | ~2-4 KB |
| Triggers and metadata | ~0.2-0.5 KB |
| **Total (MC)** | **~5-10 KB** |
| **Total (Data, no gen)** | **~3-6 KB** |

With LZMA-9 compression, typical output files are 50-70% smaller on disk than
the uncompressed sizes above would suggest. A 10k-event MC file is typically
30-60 MB.

---

## Processing Sequence

The `MC_2024_Scouting.py` configuration schedules two NANO paths:

```python
process.nanoAOD_step0 = cms.Path(process.nanogenSequence)      # Gen-level
process.nanoAOD_step1 = cms.Path(process.scoutingNanoSequence)  # Scouting reco
```

Customizations are applied in order:
1. `addScoutingPFCandidate(process)` -- PF candidate translation
2. `customiseScoutingNano(process)` -- standard scouting NanoAOD tables
3. `customiseScoutingNanoFromMini(process)` -- MiniAOD-specific scouting setup
4. `addAll(process)` -- ScoutingTranslator reclustered jets, vertices, V0, beam spot
5. `customizeNanoGENFromMini(process)` -- generator-level tables from MiniAOD

The trigger results are explicitly kept via:
```python
process.NANOAODSIMoutput.outputCommands.append("keep edmTriggerResults_*_*_*")
```
