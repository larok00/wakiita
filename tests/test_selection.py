"""Run with: python -m unittest discover -s tests"""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins/wakiita/scripts"))
from selection import select


def route(name, when, overlays=()):
    return {
        "id": name, "when": when, "requires": ["base.ready"],
        "instructions": "AGENTS.md", "interactive": False,
        "overlays": list(overlays),
    }


def overlay(name, when):
    return {"id": name, "when": when, "instructions": "AGENTS.md"}


def manifest(*routes):
    return {"schemaVersion": 1, "id": "editor", "provides": ["editor.ready"],
            "routes": list(routes)}


class SelectionTests(unittest.TestCase):
    def test_first_match_wins_even_with_unmet_requirements(self):
        data = manifest(route("preferred", {}), route("fallback", {}))
        self.assertEqual(select(data, {}), {
            "status": "selected", "route": "preferred", "overlays": [],
            "missing_facts": [],
        })

    def test_unknown_fact_prevents_premature_fallback(self):
        data = manifest(route("desktop", {"os": "windows", "machine": "desktop"}),
                        route("windows", {"os": "windows"}))
        result = select(data, {"os": "windows"})
        self.assertEqual(result["status"], "unresolved")
        self.assertIsNone(result["route"])
        self.assertEqual(result["missing_facts"], ["machine"])

    def test_known_mismatch_overrides_unknown_regardless_of_key_order(self):
        for when in ({"machine": "desktop", "os": "windows"},
                     {"os": "windows", "machine": "desktop"}):
            with self.subTest(when=when):
                data = manifest(route("desktop", when), route("fallback", {}))
                self.assertEqual(select(data, {"os": "linux"})["route"], "fallback")

    def test_explicitly_absent_profile_allows_fallback(self):
        data = manifest(route("desktop", {"machine": "desktop"}), route("general", {}))
        self.assertEqual(select(data, {"machine": None})["route"], "general")

    def test_no_match_is_unsupported(self):
        data = manifest(route("linux", {"os": "linux"}))
        self.assertEqual(select(data, {"os": "windows"})["status"], "unsupported")

    def test_conditions_are_exact_and_conjunctive(self):
        data = manifest(route("specific", {"os": "linux", "environment": "omarchy"}),
                        route("general", {}))
        for target in ({"os": "windows", "environment": "omarchy"},
                       {"os": "linux", "environment": "other"}):
            self.assertEqual(select(data, target)["route"], "general")
        self.assertEqual(select(data, {"os": "linux", "environment": "omarchy"})["route"],
                         "specific")

    def test_all_matching_overlays_preserve_order(self):
        overlays = [overlay("shared", {}), overlay("desktop", {"machine": "desktop"}),
                    overlay("laptop", {"machine": "laptop"}), overlay("last", {})]
        data = manifest(route("general", {}, overlays))
        self.assertEqual(select(data, {"machine": "desktop"})["overlays"],
                         ["shared", "desktop", "last"])

    def test_unknown_overlays_return_grouped_facts_without_partial_selection(self):
        overlays = [overlay("shared", {}), overlay("profile", {"machine": "desktop"}),
                    overlay("browser", {"browser": "chrome"}),
                    overlay("profile-again", {"machine": "desktop"})]
        result = select(manifest(route("general", {}, overlays)), {})
        self.assertEqual(result, {"status": "unresolved", "route": "general",
                                 "overlays": [], "missing_facts": ["browser", "machine"]})

    def test_mismatched_overlay_does_not_request_irrelevant_fact(self):
        data = manifest(route("general", {}, [
            overlay("desktop", {"machine": "desktop", "os": "windows"})]))
        self.assertEqual(select(data, {"os": "linux"})["status"], "selected")

    def test_absent_profile_excludes_machine_overlays(self):
        data = manifest(route("general", {}, [overlay("desktop", {"machine": "desktop"})]))
        self.assertEqual(select(data, {"machine": None})["overlays"], [])

    def test_unselected_routes_do_not_request_facts(self):
        data = manifest(route("first", {}), route("later", {"browser": "chrome"},
                        [overlay("desktop", {"machine": "desktop"})]))
        self.assertEqual(select(data, {})["status"], "selected")

    def test_optional_overlays_and_inputs_unchanged(self):
        data = manifest(route("general", {}))
        del data["routes"][0]["overlays"]
        target = {"machine": None}
        original = copy.deepcopy((data, target))
        self.assertEqual(select(data, target)["overlays"], [])
        self.assertEqual((data, target), original)


if __name__ == "__main__":
    unittest.main()
