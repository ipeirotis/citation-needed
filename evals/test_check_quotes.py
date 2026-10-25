"""Deterministic, offline tests for the quotation-presence prototype.

Run from the repository root with:
    python3 -B -m unittest discover -s evals -p 'test_check_quotes.py' -v
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_quotes.py"
SPEC = importlib.util.spec_from_file_location("check_quotes", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class NormalizationTests(unittest.TestCase):
    def test_whitespace_and_original_spans(self):
        source = " \talpha\r\n\u00a0\f beta  "
        normalized, spans = checker.normalize(source)
        self.assertEqual(normalized, "alpha beta")
        self.assertEqual(len(spans), len(normalized))
        self.assertEqual(source[spans[0][0]:spans[-1][1]], "alpha\r\n\u00a0\f beta")
        self.assertEqual(source[slice(*spans[5])], "\r\n\u00a0\f ")

    def test_composition_and_typography_preserve_original_offsets(self):
        source = "‘cafe\u0301’ \ufb03 \u1100\u1161\u11a8"
        normalized, spans = checker.normalize(source)
        self.assertEqual(normalized, "'café' ffi 각")
        accent = normalized.index("é")
        self.assertEqual(source[slice(*spans[accent])], "e\u0301")
        ligature = normalized.index("ffi")
        self.assertEqual(spans[ligature:ligature + 3], [(8, 9)] * 3)
        self.assertEqual(source[slice(*spans[-1])], "\u1100\u1161\u11a8")

    def test_normalization_does_not_rewrite_meaningful_characters(self):
        for source in ("Rate", "−3", "μ", "A—B", "１２", "hy-\nphen", "soft\u00adhyphen"):
            with self.subTest(source=source):
                normalized, _ = checker.normalize(source)
                self.assertEqual(normalized, source.replace("\n", " "))

    def test_empty_normalization(self):
        for source in ("", " \n\t\u00a0"):
            with self.subTest(source=repr(source)):
                self.assertEqual(checker.normalize(source), ("", []))

    def test_accented_ligature_is_composed_after_expansion(self):
        source = "La ﬁ\u0301sica"
        normalized, spans = checker.normalize(source)
        self.assertEqual(normalized, "La física")
        self.assertEqual(checker.normalize(normalized)[0], normalized)
        accent = normalized.index("í")
        self.assertEqual(source[slice(*spans[accent])], "ﬁ\u0301")


class QuoteTests(unittest.TestCase):
    def check(self, source, quote):
        return checker.check_quote(source, quote, "test")

    def test_exact_match_and_original_character_locations(self):
        source = "😀 prefix\nA literal quotation.\nSuffix"
        quote = "A literal quotation."
        result = self.check(source, quote)
        self.assertEqual(result["status"], "exact")
        self.assertTrue(result["found"])
        self.assertEqual(result["occurrences"], 1)
        location = result["locations"][0]
        self.assertEqual(location["start"], source.index(quote))
        self.assertEqual(location["end"], source.index(quote) + len(quote))
        self.assertEqual(location["source_text"], quote)
        self.assertEqual(location["mode"], "exact")
        self.assertEqual((location["line_start"], location["line_end"]), (2, 2))
        self.assertIn(quote, location["context"])

    def test_normalized_match_reports_raw_passage_and_lines(self):
        source = "Prefix\n‘The cafe\u0301’\r\n\tuses \ufb01ne methods.\nSuffix"
        quote = "'The café' uses fine methods."
        result = self.check(source, quote)
        self.assertEqual(result["status"], "normalized")
        self.assertTrue(result["found"])
        location = result["locations"][0]
        self.assertEqual(location["source_text"], "‘The cafe\u0301’\r\n\tuses \ufb01ne methods.")
        self.assertEqual(location["mode"], "normalized")
        self.assertEqual(source[location["start"]:location["end"]], location["source_text"])
        self.assertEqual((location["line_start"], location["line_end"]), (2, 3))

    def test_cached_normalization_has_identical_results(self):
        source, quote = "The\n\tﬁnding is clear.", "The finding is clear."
        self.assertEqual(
            self.check(source, quote),
            checker.check_quote(source, quote, "test", checker.normalize(source)),
        )

    def test_accented_ligature_matches_composed_quotation(self):
        result = self.check("La ﬁ\u0301sica", "La física")
        self.assertTrue(result["found"])
        self.assertEqual(result["status"], "normalized")
        self.assertEqual(result["locations"][0]["source_text"], "La ﬁ\u0301sica")

    def test_changed_negation_case_numbers_and_order_do_not_match(self):
        cases = [
            ("The treatment does not cause harm.", "The treatment does cause harm."),
            ("The treatment does cause harm.", "The treatment does not cause harm."),
            ("The result is supported.", "the result is supported."),
            ("The score is 28.4 BLEU.", "The score is 28.5 BLEU."),
            ("alpha beta gamma", "gamma beta alpha"),
            ("x ≥ 3", "x > 3"),
            ("micro μ", "micro µ"),
        ]
        for source, quote in cases:
            with self.subTest(source=source, quote=quote):
                result = self.check(source, quote)
                self.assertFalse(result["found"])
                self.assertEqual(result["status"], "not_found")
                self.assertEqual(result["locations"], [])

    def test_word_and_identifier_fragments_do_not_match(self):
        for source, quote in [
            ("unsupported", "supported"), ("catastrophe", "cat"),
            ("pre_word", "word"), ("word_suffix", "word"),
            ("αbeta", "beta"), ("betaα", "beta"),
            ("x\u0301", "x"), ("28.4", "8.4"), ("123", "12"),
        ]:
            with self.subTest(source=source, quote=quote):
                self.assertFalse(self.check(source, quote)["found"])

    def test_signed_decimal_and_grouped_number_fragments_do_not_match(self):
        for source, quote in [
            ("-3", "3"), ("+3", "3"), ("−3", "3"),
            ("1.25", "25"), ("1.25", "1"),
            ("1,250", "250"), ("1,250", "1"),
            ("-1.25", "1.25"), ("3e-5", "3"),
            ("The value is .5.", "5"), ("The value is -.5.", ".5"),
        ]:
            with self.subTest(source=source, quote=quote):
                self.assertFalse(self.check(source, quote)["found"])

    def test_sentence_period_cannot_truncate_a_decimal(self):
        result = self.check("The rate was 3.14%.", "The rate was 3.")
        self.assertFalse(result["found"])

    def test_hyphenated_line_break_is_not_silently_repaired(self):
        self.assertFalse(self.check("A hy-\nphenated word.", "A hyphenated word.")["found"])

    def test_ellipses_and_bracketed_edits_require_review(self):
        source = "Alpha beta gamma delta."
        for quote in ("Alpha ... delta.", "Alpha … delta.", "Alpha [omitted] delta.",
                      "Alpha [] delta.", "delta. ... Alpha"):
            with self.subTest(quote=quote):
                result = self.check(source, quote)
                self.assertFalse(result["found"])
                self.assertEqual(result["status"], "manual_review")
                self.assertIn("not matched as wildcards", result["reason"])

    def test_literal_ellipsis_and_brackets_are_allowed(self):
        for quote in ("Alpha ... delta.", "Alpha … delta.", "Alpha [sic] delta."):
            with self.subTest(quote=quote):
                result = self.check("Prefix " + quote + " Suffix", quote)
                self.assertTrue(result["found"])
                self.assertEqual(result["status"], "exact")

    def test_literal_edited_notation_can_match_after_whitespace_normalization(self):
        result = self.check("Alpha\n... [sic] delta.", "Alpha ... [sic] delta.")
        self.assertEqual(result["status"], "normalized")
        self.assertTrue(result["found"])

    def test_multiple_occurrences_require_location_review(self):
        source = "echo\necho\necho"
        result = self.check(source, "echo")
        self.assertEqual(result["occurrences"], 3)
        self.assertEqual([loc["start"] for loc in result["locations"]], [0, 5, 10])
        self.assertEqual([loc["line_start"] for loc in result["locations"]], [1, 2, 3])
        self.assertIn("Multiple occurrences", result["review"])

    def test_multiple_normalized_occurrences_keep_raw_locations(self):
        source = "alpha\nbeta\nalpha\tbeta"
        result = self.check(source, "alpha beta")
        self.assertEqual(result["status"], "normalized")
        self.assertEqual(result["occurrences"], 2)
        self.assertEqual([loc["source_text"] for loc in result["locations"]],
                         ["alpha\nbeta", "alpha\tbeta"])

    def test_mixed_exact_and_normalized_occurrences_are_all_counted(self):
        source = "alpha beta\nalpha\tbeta\nalpha\nbeta"
        result = self.check(source, "alpha beta")
        self.assertEqual(result["status"], "normalized")
        self.assertEqual(result["occurrences"], 3)
        self.assertEqual([loc["mode"] for loc in result["locations"]],
                         ["exact", "normalized", "normalized"])
        self.assertEqual([loc["source_text"] for loc in result["locations"]],
                         ["alpha beta", "alpha\tbeta", "alpha\nbeta"])
        self.assertIn("Multiple occurrences", result["review"])

    def test_location_limit_does_not_truncate_occurrence_count(self):
        count = checker.MAX_LOCATIONS + 3
        result = self.check("\n".join(["echo"] * count), "echo")
        self.assertEqual(result["occurrences"], count)
        self.assertEqual(len(result["locations"]), checker.MAX_LOCATIONS)
        self.assertEqual(result["status"], "normalized")
        self.assertTrue(all(loc["mode"] == "exact" for loc in result["locations"]))

    def test_invalid_quote_api_raises_controlled_error(self):
        for quote in ("", " \n\t\u00a0", None, 7):
            with self.subTest(quote=quote):
                with self.assertRaises(ValueError):
                    self.check("source text", quote)

    def test_missing_quote_is_presence_failure_not_support_verdict(self):
        result = self.check("The extraction is partial.", "Absent passage")
        self.assertEqual(result["status"], "not_found")
        self.assertIn("not an unsupported-claim verdict", result["reason"])


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="quote-check-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.write("source.txt", "The source supports this quotation.\n")

    def write(self, name, content):
        path = self.root / name
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return path

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              cwd=self.root, capture_output=True, text=True, check=False)

    def report(self, completed, expected_code):
        self.assertEqual(completed.returncode, expected_code, completed.stderr + completed.stdout)
        self.assertEqual(completed.stderr, "")
        report = json.loads(completed.stdout)
        self.assertEqual(report["schema"], checker.SCHEMA)
        return report

    def test_success_report_identifies_original_bytes_and_limitations(self):
        report = self.report(self.run_cli("--source", self.source, "--quote", "this quotation"), 0)
        raw = self.source.read_bytes()
        self.assertEqual(report["source"], {
            "path": str(self.source), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
        })
        self.assertEqual(report["summary"], {"total": 1, "found": 1})
        self.assertIn("zero-based Python character offsets", report["offsets"])
        self.assertIn("does not establish source identity", report["limitation"])

    def test_quote_file_and_mixed_batch(self):
        quote_file = self.write("quote.txt", "this quotation")
        report = self.report(self.run_cli("--source", self.source, "--quote-file", quote_file), 0)
        self.assertEqual(report["results"][0]["id"], "1")
        batch = self.write("quotes.json", json.dumps([
            "this quotation", {"id": "missing", "quote": "an absent passage"},
            {"id": "edit", "quote": "The ... quotation."},
        ]))
        report = self.report(self.run_cli("--source", self.source, "--quotes-json", batch), 1)
        self.assertEqual(report["summary"], {"total": 3, "found": 1})
        self.assertEqual([r["id"] for r in report["results"]], ["1", "missing", "edit"])
        self.assertEqual([r["status"] for r in report["results"]],
                         ["exact", "not_found", "manual_review"])

    def test_digest_checks_original_utf8_bytes_including_crlf(self):
        source = self.write("unicode.txt", "cafe\u0301\r\n\u00a0ﬁne".encode("utf-8"))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        report = self.report(self.run_cli("--source", source, "--quote", "café fine",
                                         "--expected-sha256", digest.upper()), 0)
        self.assertEqual(report["source"]["sha256"], digest)
        self.assertEqual(report["results"][0]["status"], "normalized")

    def test_digest_mismatch_and_malformed_digest_are_errors(self):
        for digest in ("0" * 64, "g" * 64, "0" * 63, "", "sha256:" + "0" * 64):
            with self.subTest(digest=digest):
                report = self.report(self.run_cli("--source", self.source, "--quote", "source",
                                                 "--expected-sha256", digest), 2)
                self.assertEqual(report["status"], "error")
                self.assertNotIn("results", report)

    def test_missing_and_non_file_inputs_are_errors(self):
        for path in (self.root / "absent.txt", self.root):
            with self.subTest(path=path):
                report = self.report(self.run_cli("--source", path, "--quote", "source"), 2)
                self.assertEqual(report["status"], "error")
        report = self.report(self.run_cli("--source", self.source, "--quote-file",
                                         self.root / "absent-quote.txt"), 2)
        self.assertEqual(report["status"], "error")

    def test_invalid_utf8_empty_nul_pdf_and_html_sources_are_errors(self):
        cases = {
            "invalid.txt": b"\xff", "empty.txt": b"", "whitespace.txt": b" \n\t",
            "nul.txt": b"source\x00text", "paper.pdf": b"source text",
            "disguised.txt": b"%PDF-1.7 source text", "page.HTML": b"<p>source text</p>",
        }
        for name, raw in cases.items():
            with self.subTest(name=name):
                path = self.write(name, raw)
                report = self.report(self.run_cli("--source", path, "--quote", "source"), 2)
                self.assertEqual(report["status"], "error")

    def test_empty_quotes_are_input_errors(self):
        for quote in ("", " \n\t\u00a0"):
            with self.subTest(quote=repr(quote)):
                report = self.report(self.run_cli("--source", self.source, "--quote", quote), 2)
                self.assertEqual(report["status"], "error")

    def test_malformed_batches_are_atomic_input_errors(self):
        malformed = [
            None, {}, "quotation", [], [""], [" \n"], [None], [7],
            [{"quote": "source", "extra": True}], [{}],
            [{"id": "", "quote": "source"}], [{"id": " ", "quote": "source"}],
            [{"id": 7, "quote": "source"}], [{"id": True, "quote": "source"}],
            [{"id": "a", "quote": "source"}, {"id": "a", "quote": "quotation"}],
            ["source", {"id": "1", "quote": "quotation"}],
            ["source", {"id": "later", "quote": 7}],
        ]
        for index, entries in enumerate(malformed):
            with self.subTest(entries=entries):
                path = self.write("batch.json", json.dumps(entries))
                report = self.report(self.run_cli("--source", self.source, "--quotes-json", path), 2)
                self.assertEqual(report["status"], "error")
                self.assertNotIn("results", report)
        invalid_json = self.write("batch.json", '["source",')
        report = self.report(self.run_cli("--source", self.source, "--quotes-json", invalid_json), 2)
        self.assertEqual(report["status"], "error")

    def test_argparse_rejects_missing_and_conflicting_arguments(self):
        for args in ((), ("--source", self.source), ("--quote", "source"),
                     ("--source", self.source, "--quote", "source", "--quote-file", self.source),
                     ("--source", self.source, "--quote", "source", "--unknown")):
            with self.subTest(args=args):
                completed = self.run_cli(*args)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, "")
                self.assertIn("usage:", completed.stderr)

    def test_cli_is_read_only(self):
        batch = self.write("batch.json", json.dumps(["source", "absent"]))
        before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                  for path in self.root.iterdir()}
        self.report(self.run_cli("--source", self.source, "--quotes-json", batch), 1)
        after = {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                 for path in self.root.iterdir()}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
