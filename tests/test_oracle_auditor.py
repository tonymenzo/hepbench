"""
# tests/test_oracle_auditor.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Tests for scripts/audit_oracle_access.py: a synthetic run with one
honest trial and several cheating trials must flag exactly the
cheaters, and --zero must rewrite their scores.
"""

import gzip
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "audit_oracle_access", ROOT / "scripts" / "audit_oracle_access.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def _write_transcript(trial_dir: Path, calls: list):
    trial_dir.mkdir(parents=True)
    with gzip.open(trial_dir / "transcript.jsonl.gz", "wt") as fh:
        for c in calls:
            fh.write(json.dumps({"type": "tool_call", "t": 1.0,
                                 "name": c[0], "args": c[1]}) + "\n")


HONEST = [
    ("runpython", {"code": "import sympy as sp; print(sp.sqrt(2))"}),
    ("writefile", {"path": "results/answer.json", "content": "{}"}),
]
CHEAT_DIRECT = [
    ("runpython", {"code": "print(open('ground_truth/truth.json').read())"}),
]
CHEAT_TRAVERSAL = [
    ("runpython", {"code": "open('../../../../../benchmarks/symbolic/x/"
                           "ground_truth/truth.json')"}),
]
CHEAT_SEARCH = [
    ("runpython", {"code": "import glob; glob.glob('/home/**/truth.json')"}),
]
CHEAT_ABS = [
    ("runpython", {"code": "open('/home/u/kitchen/hepbench/benchmarks/"
                           "symbolic/x/ground_truth/truth.json')"}),
]


def _make_run(tmp_path) -> Path:
    run = tmp_path / "run"
    (run / "trials").mkdir(parents=True)
    _write_transcript(run / "trials" / "honest", HONEST)
    _write_transcript(run / "trials" / "cheat_direct", CHEAT_DIRECT)
    _write_transcript(run / "trials" / "cheat_traversal", CHEAT_TRAVERSAL)
    _write_transcript(run / "trials" / "cheat_search", CHEAT_SEARCH)
    _write_transcript(run / "trials" / "cheat_abs", CHEAT_ABS)
    trials = [
        {"trial_id": "honest", "score": 1.0, "ok": True},
        {"trial_id": "cheat_direct", "score": 1.0, "ok": True},
        {"trial_id": "cheat_traversal", "score": 1.0, "ok": True},
        {"trial_id": "cheat_search", "score": 1.0, "ok": True},
        {"trial_id": "cheat_abs", "score": 1.0, "ok": True},
    ]
    (run / "trials.jsonl").write_text(
        "\n".join(json.dumps(t) for t in trials) + "\n")
    return run


def test_flags_only_cheaters(tmp_path):
    run = _make_run(tmp_path)
    results = audit.audit_run(run)
    by = {r["trial"]: r["flagged"] for r in results}
    assert by["honest"] is False
    assert by["cheat_direct"] is True
    assert by["cheat_traversal"] is True
    assert by["cheat_search"] is True
    assert by["cheat_abs"] is True


def test_zero_rewrites_flagged(tmp_path):
    run = _make_run(tmp_path)
    results = audit.audit_run(run)
    n = audit.zero_flagged(run, results)
    assert n == 4
    rows = {json.loads(l)["trial_id"]: json.loads(l)
            for l in (run / "trials.jsonl").read_text().splitlines()}
    assert rows["honest"]["score"] == 1.0
    assert rows["honest"].get("oracle_flagged") is not True
    for t in ("cheat_direct", "cheat_traversal", "cheat_search", "cheat_abs"):
        assert rows[t]["score"] == 0.0
        assert rows[t]["ok"] is False
        assert rows[t]["oracle_flagged"] is True
    assert (run / "trials.jsonl.orig").is_file()


def test_main_exit_code(tmp_path):
    run = _make_run(tmp_path)
    assert audit.main([str(run)]) == 1          # flagged -> nonzero
    honest = tmp_path / "clean"
    (honest / "trials").mkdir(parents=True)
    _write_transcript(honest / "trials" / "t0", HONEST)
    (honest / "trials.jsonl").write_text(
        json.dumps({"trial_id": "t0", "score": 1.0, "ok": True}) + "\n")
    assert audit.main([str(honest)]) == 0       # clean -> zero
