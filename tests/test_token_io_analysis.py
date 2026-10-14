"""
# tests/test_token_io_analysis.py is a part of HEPBench.
# Copyright (C) 2026 HEPBench authors (see AUTHORS for details).
# HEPBench is licensed under the GNU GPL v3 or later, see LICENSE for details.
"""
"""
Sanity tests for scripts/token_io_analysis.py: per-arm aggregation,
harness separation (closed-book vs open core_only), and the win-cost
metric.
"""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "token_io_analysis", ROOT / "scripts" / "token_io_analysis.py")
tio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tio)


def _run(tmp_path, trials, resolution=None):
    rd = tmp_path / "run"
    rd.mkdir()
    (rd / "trials.jsonl").write_text(
        "\n".join(json.dumps(t) for t in trials) + "\n")
    if resolution is not None:
        (rd / "manifest.json").write_text(json.dumps({"resolution": resolution}))
    return rd


def test_arm_aggregation_and_tools(tmp_path):
    trials = [
        {"model": "m", "condition": "core_only", "harness": "orchestral/litellm",
         "input_tokens": 100, "output_tokens": 10, "tool_calls": 2, "score": 1.0},
        {"model": "m", "condition": "core_only", "harness": "orchestral/litellm",
         "input_tokens": 300, "output_tokens": 30, "tool_calls": 3, "score": 0.0},
        {"model": "m", "condition": "tools_nda", "harness": "orchestral/litellm",
         "input_tokens": 800, "output_tokens": 20, "tool_calls": 4, "score": 1.0},
    ]
    resolution = [
        {"loadout": "core_only", "sources": []},
        {"loadout": "tools_nda",
         "sources": [{"tools": ["a", "b", "c", "d", "e", "f", "g", "h"]}]},
    ]
    rd = _run(tmp_path, trials, resolution)
    groups, tmap = tio.collect([rd])
    rows = {r["arm"]: r for r in tio.summarize(groups, tmap)}
    assert tmap["tools_nda"] == 8
    assert rows["core_only"]["n_tools"] == 0
    assert rows["tools_nda"]["n_tools"] == 8
    # in_per_call = total input / total calls = (100+300)/(2+3) = 80
    assert rows["core_only"]["in_per_call"] == 80
    # reach is the mean score
    assert rows["core_only"]["reach"] == 0.5
    # in_per_win uses only score==1.0 trials
    assert rows["core_only"]["in_per_win"] == 100
    assert rows["tools_nda"]["in_per_win"] == 800


def test_closed_harness_is_separated(tmp_path):
    trials = [
        {"model": "m", "condition": "core_only", "harness": "orchestral/litellm",
         "input_tokens": 500, "output_tokens": 50, "tool_calls": 5, "score": 1.0},
        {"model": "m", "condition": "core_only",
         "harness": "orchestral/litellm_closed",
         "input_tokens": 50, "output_tokens": 8000, "tool_calls": 0, "score": 0.0},
    ]
    rd = _run(tmp_path, trials)
    groups, tmap = tio.collect([rd])
    arms = {r["arm"] for r in tio.summarize(groups, tmap)}
    assert "core_only" in arms
    assert "core_only (closed)" in arms


def test_in_per_win_inf_when_no_win(tmp_path):
    trials = [
        {"model": "m", "condition": "tools_eda", "harness": "orchestral/litellm",
         "input_tokens": 9000, "output_tokens": 100, "tool_calls": 3, "score": 0.4},
    ]
    rd = _run(tmp_path, trials)
    groups, tmap = tio.collect([rd])
    row = tio.summarize(groups, tmap)[0]
    assert row["in_per_win"] == float("inf")
    assert row["wins"] == 0
