"""Per-dataset splitting overrides — the SUBMITREFUSED escape hatch.

CRAB's TaskWorker refuses any task whose input dataset has a block carrying
more than 100,000 lumis, and it does so AFTER the client prints "Success: Your
task has been delivered". So the failure is invisible in crab.log and the only
symptom is a missing output file. WtoLNu-4Jets_Bin-4J sat in that state for
eleven days. FileBased splitting is the only way through, because it is the
only mode that never looks lumi information up.
"""
import crabby


def card(data=False, overrides=None):
    return {"data": data, "splitting_overrides": overrides or []}


DS_4J = ("/WtoLNu-4Jets_Bin-4J_TuneCP5_13p6TeV_madgraphMLM-pythia8"
         "/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM")
DS_3J = DS_4J.replace("Bin-4J", "Bin-3J")

FILEBASED = [{"match": "WtoLNu-4Jets_Bin-4J", "splitting": "FileBased",
              "unitsPerJob": 1}]


class TestDefaults:
    def test_mc_defaults_to_automatic(self):
        assert crabby.resolve_splitting(card(), DS_4J) == ("Automatic", None)

    def test_data_defaults_to_lumibased(self):
        assert crabby.resolve_splitting(card(data=True), DS_4J) == ("LumiBased", None)

    def test_a_card_with_no_overrides_key_at_all_still_works(self):
        # older cards predate the feature; they must not KeyError
        assert crabby.resolve_splitting({"data": False}, DS_4J) == ("Automatic", None)

    def test_an_explicit_none_is_treated_as_empty(self):
        assert crabby.resolve_splitting(
            {"data": False, "splitting_overrides": None}, DS_4J) == ("Automatic", None)


class TestMatching:
    def test_the_matching_dataset_gets_the_override(self):
        assert crabby.resolve_splitting(card(overrides=FILEBASED), DS_4J) == \
            ("FileBased", 1)

    def test_a_SIBLING_dataset_is_untouched(self):
        # the whole point: 3J is fine and must stay on Automatic. A match that
        # leaked across stems would silently re-split eight healthy datasets.
        assert crabby.resolve_splitting(card(overrides=FILEBASED), DS_3J) == \
            ("Automatic", None)

    def test_first_matching_rule_wins(self):
        rules = [{"match": "Bin-4J", "splitting": "FileBased", "unitsPerJob": 1},
                 {"match": "Bin-4J", "splitting": "LumiBased", "unitsPerJob": 99}]
        assert crabby.resolve_splitting(card(overrides=rules), DS_4J) == ("FileBased", 1)

    def test_a_rule_with_no_match_key_is_ignored_not_applied_to_everything(self):
        rules = [{"splitting": "FileBased", "unitsPerJob": 1}]
        assert crabby.resolve_splitting(card(overrides=rules), DS_4J) == ("Automatic", None)

    def test_an_empty_match_string_is_ignored(self):
        # "" is a substring of every dataset -- it must NOT match all of them
        rules = [{"match": "", "splitting": "FileBased", "unitsPerJob": 1}]
        assert crabby.resolve_splitting(card(overrides=rules), DS_4J) == ("Automatic", None)

    def test_a_rule_may_set_units_without_changing_the_mode(self):
        rules = [{"match": "Bin-4J", "unitsPerJob": 20}]
        assert crabby.resolve_splitting(card(overrides=rules), DS_4J) == ("Automatic", 20)

    def test_data_override_carries_its_own_units(self):
        rules = [{"match": "Run2024G", "splitting": "FileBased", "unitsPerJob": 10}]
        assert crabby.resolve_splitting(card(data=True, overrides=rules),
                                        "/ScoutingPFRun3/Run2024G-v1/HLTSCOUT") == \
            ("FileBased", 10)
