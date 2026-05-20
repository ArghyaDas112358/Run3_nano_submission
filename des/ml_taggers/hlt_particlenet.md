# HLT ParticleNet: AK4 and AK8 Taggers

## Architecture: Dynamic Graph CNN

ParticleNet is based on the Dynamic Graph Convolutional Neural Network (DGCNN)
architecture, adapted for jet classification at CMS. The core idea is to construct
a graph where each node represents a particle within the jet, and edges connect
neighboring particles in a learned feature space.

Key architectural elements:

- **EdgeConv blocks**: At each layer, a k-nearest-neighbors graph is constructed in
  the current feature space. Edge features (differences between connected nodes) are
  processed through a shared MLP, and node features are updated by aggregating over
  their neighbors.

- **Dynamic graph**: The neighbor graph is recomputed after each EdgeConv block,
  allowing the network to discover different particle relationships at different
  abstraction levels.

- **Global pooling**: After several EdgeConv layers, all node features are aggregated
  into a single jet-level representation via channel-wise global average pooling.

- **Classification head**: A fully connected network maps the jet representation to
  output class probabilities.

ParticleNet is lighter-weight than transformer-based architectures, making it suitable
for HLT deployment where inference latency is critical.

## HLT-Level Score Computation

In the scouting NanoAOD pipeline, ParticleNet scores are **not** taken directly from
pre-computed HLT decisions. Instead, the HLT ParticleNet model is re-run offline on
the translated scouting objects. This is necessary because:

1. Scouting jets are **reclustered** from translated PF candidates, potentially
   differing from the original HLT jet clustering.
2. The HLT does not store per-jet tagger scores in the scouting data stream.
3. Re-running the model ensures consistency between jet definitions and tagger inputs.

The feature extraction uses `use_hlt_features = True`, which activates the HLT-compatible
feature set. This means the features are computed in the same format as the HLT would
use, even though the computation happens offline.

## Feature Extraction: DeepBoostedJetTagInfo

Both AK4 and AK8 ParticleNet use the `DeepBoostedJetTagInfoProducer` for feature
extraction. This producer:

1. Collects PF candidates within the jet cone.
2. Extracts per-particle features (kinematics, particle ID, impact parameters).
3. Applies feature normalization using parameters from a `preprocess.json` file.
4. Packages features into a flat representation consumed by the ONNX model.

Key configuration differences between AK4 and AK8:

| Parameter | AK4 | AK8 |
|-----------|-----|-----|
| `jet_radius` | 0.4 | 0.8 |
| `min_jet_pt` | 5.0 GeV | 200.0 GeV |
| `max_jet_eta` | 2.6 | 2.5 |
| `use_hlt_features` | True | True |
| `use_scouting_features` | False | False |
| `sort_by_sip2dsig` | False | False |
| `include_neutrals` | True | True |
| `min_pt_for_pfcandidates` | 0.1 GeV | 0.1 GeV |
| `min_pt_for_track_properties` | 0.95 GeV | 0.95 GeV |

Both use the same input collections:
- `pf_candidates`: `recoScoutingPFCandidate`
- `secondary_vertices`: `scoutingDeepInclusiveMergedVerticesPF`
- `vertices`: `scoutingVerticesPFFilter`
- `vertex_associator`: PV association from `PFCandidatePrimaryVertexSorter`

## HLT ParticleNet AK4

### Model

- **Path**: `RecoBTag/Combined/data/HLT/ParticleNetAK4/V01/particle-net.onnx`
- **Preprocessing**: `RecoBTag/Combined/data/HLT/ParticleNetAK4/V01/preprocess.json`
- **Producer**: `BoostedJetONNXJetTagsProducer`
- **Module name**: `scoutingPFJetReclusterHLTParticleNetONNXJetTags`

### 7 Output Discriminants

| Output | Description | NanoAOD Branch |
|--------|-------------|---------------|
| `probtauhp` | Hadronic tau (positive charge) | `ScoutingPFJetRecluster2_hltPNet_probtauhp` |
| `probtauhm` | Hadronic tau (negative charge) | `ScoutingPFJetRecluster2_hltPNet_probtauhm` |
| `probb` | b quark | `ScoutingPFJetRecluster2_hltPNet_probb` |
| `probc` | c quark | `ScoutingPFJetRecluster2_hltPNet_probc` |
| `probuds` | Light quark (u, d, s) | `ScoutingPFJetRecluster2_hltPNet_probuds` |
| `probg` | Gluon | `ScoutingPFJetRecluster2_hltPNet_probg` |
| `ptcorr` | pT correction factor | (not stored in NanoAOD) |

The `ptcorr` output provides a jet energy correction factor but is not propagated
to the NanoAOD output tables.

### Selection Criteria

Scores are computed only for jets satisfying pT >= 5 GeV and |eta| <= 2.6. Jets
outside this acceptance have all HLT PNet scores set to -1 in the NanoAOD.

## HLT ParticleNet AK8

### Model

- **Path**: `RecoBTag/Combined/data/HLT/ParticleNetAK8/V01/particle-net.onnx`
- **Preprocessing**: `RecoBTag/Combined/data/HLT/ParticleNetAK8/V01/preprocess.json`
- **Producer**: `BoostedJetONNXJetTagsProducer`
- **Module name**: `scoutingFatPFJetReclusterHLTParticleNetONNXJetTagsAK8`

### 10 Output Discriminants

The AK8 model is designed to classify boosted heavy resonance decays:

| Output | Description | NanoAOD Branch |
|--------|-------------|---------------|
| `probHtt` | H -> tau_h tau_h | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHtt` |
| `probHtm` | H -> tau_h tau_mu | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHtm` |
| `probHte` | H -> tau_h tau_e | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHte` |
| `probHbb` | H -> bb | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHbb` |
| `probHcc` | H -> cc | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHcc` |
| `probHqq` | H -> qq (light) | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHqq` |
| `probHgg` | H -> gg | `ScoutingFatPFJetRecluster2_hltPNetAK8_probHgg` |
| `probQCD2hf` | QCD with 2 heavy-flavor quarks | `ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD2hf` |
| `probQCD1hf` | QCD with 1 heavy-flavor quark | `ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD1hf` |
| `probQCD0hf` | QCD with 0 heavy-flavor quarks | `ScoutingFatPFJetRecluster2_hltPNetAK8_probQCD0hf` |

### Selection Criteria

Scores are computed for jets with pT >= 200 GeV and |eta| <= 2.5. The 200 GeV
threshold reflects the boosted regime where AK8 jets contain merged decay products.

### Relevance to HH->bb(tautau)

The AK8 ParticleNet tagger is particularly relevant for the boosted HH topology:

- **Boosted H->tautau**: When the Higgs boson has high pT, its tau decay products
  merge into a single fat jet. The `probHtt`, `probHtm`, and `probHte` scores
  discriminate these from QCD backgrounds.

- **Boosted H->bb**: Similarly, `probHbb` identifies fat jets containing merged
  b-quark pairs from Higgs decay.

- **QCD background**: The three QCD categories (0hf, 1hf, 2hf) provide granular
  background classification for working point optimization.

## Propagation Through the Pipeline

The full chain for HLT ParticleNet scores in the scouting pipeline:

```
recoScoutingPFCandidate  --->  Jet Reclustering (AK4/AK8)
                                      |
                                      v
                          DeepBoostedJetTagInfoProducer
                          (feature extraction with HLT feature format)
                                      |
                                      v
                          BoostedJetONNXJetTagsProducer
                          (ONNX inference with preprocess.json normalization)
                                      |
                                      v
                          JetTag collections (per-flavor scores)
                                      |
                                      v
                          PAT jet discriminator sources
                                      |
                                      v
                          NanoAOD flat table (hltPNet_* / hltPNetAK8_* branches)
```

Both the AK4 and AK8 ParticleNet taggers are integrated into the PAT jet as
discriminator sources, alongside the UParT scores (for AK4). The PAT jet then
serves as the source for the NanoAOD flat table producer.

## Comparison: HLT ParticleNet vs UParT for AK4

Both taggers run on the same reclustered AK4 jets but differ in key respects:

| Aspect | HLT ParticleNet AK4 | UParT AK4 |
|--------|---------------------|-----------|
| Architecture | Dynamic Graph CNN | Transformer |
| pT threshold | 5 GeV | 15 GeV |
| eta acceptance | 2.6 | 2.5 |
| Feature format | HLT-style flat | Structured (CPF/NPF/SV) |
| Preprocessing | JSON-based normalization | Implicit in features |
| Flavor outputs | 7 (incl. ptcorr) | 8 |
| Tau categories | tauhp, tauhm | taum, taup |
| b sub-categories | probb only | probb, probbb, problepb |
| Model source | Central CMS (HLT) | Custom (HH->bbtautau trained) |
| NanoAOD prefix | `hltPNet_` | `scoutUParT_` |

The UParT provides finer b-jet granularity (3 b-categories vs 1) and was specifically
trained for scouting data, while HLT ParticleNet offers broader coverage (lower pT
threshold) and serves as a cross-check reference.
