"""Integrity of the dataset and of the queries over it."""
import json
import unittest

from crossmap import cli, model, query, report_html


class TestDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = model.load()

    def test_catalogue_sizes(self):
        self.assertEqual(len(self.d.all_controls("ISO")), 93)
        self.assertEqual(len(self.d.all_controls("ENS")), 73)

    def test_iso_themes(self):
        from collections import Counter
        counts = Counter(c.family for c in self.d.all_controls("ISO"))
        self.assertEqual(dict(counts), {"5": 37, "6": 8, "7": 14, "8": 34})

    def test_every_link_points_at_a_real_control(self):
        self.assertEqual(self.d.unknown_references(), [])

    def test_every_link_cites_a_known_source(self):
        self.assertEqual(self.d.unknown_sources(), [])

    def test_every_iso_control_has_a_row(self):
        rows = {r["iso"] for r in json.loads(
            (model.DATA / "mappings.json").read_text(encoding="utf-8"))["rows"]}
        self.assertEqual(rows, {c.id for c in self.d.all_controls("ISO")})

    def test_bilingual_titles_everywhere(self):
        for framework in ("ISO", "ENS", "NIS2", "DORA"):
            for control in self.d.all_controls(framework):
                self.assertTrue(control.title.get("en"), f"{control.ref} has no English title")
                self.assertTrue(control.title.get("es"), f"{control.ref} has no Spanish title")

    def test_coverage_values_are_valid(self):
        for link in self.d.links:
            self.assertIn(link.coverage, ("full", "partial", "none"))

    def test_no_correspondence_is_marked_verified_yet(self):
        """Everything starts as proposed; verification is a human act."""
        self.assertEqual(self.d.stats()["verified"], 0)

    def test_a_control_with_no_targets_is_marked_none(self):
        for iso_id, per_framework in self.d.coverage.items():
            for framework, coverage in per_framework.items():
                targets = self.d.forward.get(iso_id, {}).get(framework, [])
                if coverage == "none":
                    self.assertEqual(targets, [], f"{iso_id} -> {framework}")
                else:
                    self.assertTrue(targets, f"{iso_id} -> {framework} claims {coverage}")


class TestQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = model.load()

    def test_resolve_accepts_several_shapes(self):
        for reference in ("8.15", "ISO 8.15", "iso:8.15"):
            self.assertEqual(query.resolve(self.d, reference).id, "8.15")

    def test_resolve_finds_each_framework(self):
        self.assertEqual(query.resolve(self.d, "op.exp.8").framework, "ENS")
        self.assertEqual(query.resolve(self.d, "cir.3.2").framework, "NIS2")
        self.assertEqual(query.resolve(self.d, "art.12").framework, "DORA")
        self.assertEqual(query.resolve(self.d, "21.2.a").framework, "NIS2")

    def test_resolve_tolerates_a_bare_dora_article(self):
        self.assertEqual(query.resolve(self.d, "DORA 12").id, "art.12")

    def test_unknown_reference_is_none(self):
        self.assertIsNone(query.resolve(self.d, "no.such.thing"))

    def test_query_is_bidirectional(self):
        """From ENS to ISO and back must agree."""
        ens = query.resolve(self.d, "op.exp.8")
        iso_ids = {e["control"].id for e in query.equivalents(self.d, ens)["ISO"]}
        self.assertIn("8.15", iso_ids)
        iso = query.resolve(self.d, "8.15")
        back = {e["control"].id for e in query.equivalents(self.d, iso)["ENS"]}
        self.assertIn("op.exp.8", back)

    def test_from_one_framework_you_reach_the_other_two(self):
        found = query.equivalents(self.d, query.resolve(self.d, "art.12"))
        self.assertTrue(found["ENS"])
        self.assertTrue(found["NIS2"])
        self.assertTrue(found["ISO"])

    def test_search_ignores_accents_and_case(self):
        ids = {c.id for c in query.search(self.d, "CRIPTOGRAFIA")}
        self.assertIn("8.24", ids)
        self.assertEqual(ids, {c.id for c in query.search(self.d, "criptografía")})

    def test_search_matches_identifiers(self):
        self.assertTrue(any(c.id == "8.15" for c in query.search(self.d, "8.15")))

    def test_gaps_are_reported_for_dora_only(self):
        self.assertEqual(query.orphans(self.d, "ENS"), [])
        self.assertEqual(query.orphans(self.d, "NIS2"), [])
        self.assertTrue(query.orphans(self.d, "DORA"))

    def test_dora_gaps_are_the_supervisory_articles(self):
        gaps = {c.id for c in query.orphans(self.d, "DORA")}
        for supervisory in ("art.20", "art.21", "art.22"):
            self.assertIn(supervisory, gaps)


class TestOutputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = model.load()

    def test_html_is_self_contained_and_bilingual(self):
        page = report_html.render(self.d)
        self.assertIn("<!DOCTYPE html>", page)
        self.assertNotIn("http://", page.split("</style>")[0])
        self.assertIn('data-lang="es"', page)
        self.assertIn("op.exp.8", page)
        self.assertIn("art.12", page)

    def test_html_embeds_every_row(self):
        self.assertEqual(report_html.render(self.d).count('"iso":'), 93)

    def test_cli_show_and_gaps(self):
        self.assertEqual(cli.main(["show", "8.15", "--lang", "en"]), 0)
        self.assertEqual(cli.main(["gaps", "DORA"]), 0)
        self.assertEqual(cli.main(["stats"]), 0)

    def test_cli_verify_passes(self):
        self.assertEqual(cli.main(["verify"]), 0)

    def test_cli_reports_an_unknown_reference(self):
        self.assertEqual(cli.main(["show", "does.not.exist"]), 1)

    def test_cli_export_is_valid_json(self):
        import io
        import contextlib
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            cli.main(["export"])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(len(payload["controls"]["ISO"]), 93)


class TestSourceWatcher(unittest.TestCase):
    def test_change_detection_logic(self):
        from crossmap.sources import _changed
        old = {"ok": True, "sha256": "a", "length": 10, "etag": "1", "last_modified": "x"}
        self.assertIsNone(_changed(old, dict(old)))
        self.assertIn("content changed", _changed(old, {**old, "sha256": "b", "length": 12}))
        self.assertEqual(_changed(old, {**old, "etag": "2"}), "ETag changed")
        self.assertIsNone(_changed({}, old))          # first sighting is not a change
        self.assertIsNone(_changed(old, {"ok": False}))   # unreachable is not a change

    def test_affected_rows_are_reported(self):
        from crossmap.sources import affected_rows
        dataset = model.load()
        self.assertTrue(affected_rows(dataset, "CCN-STIC-825"))
        self.assertEqual(affected_rows(dataset, "no-such-source"), [])


if __name__ == "__main__":
    unittest.main()
