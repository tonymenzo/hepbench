"""Every number pinned in the `bare` user prompt must equal the reference's own.

The bare variant states all of its inputs in prose rather than shipping a
geometry YAML and a reference .tex, which is what makes "what was the agent
given" a single reviewable artifact. The cost is that prose can drift from the
code silently, and this session has already been bitten three times by exactly
that class of divergence -- the hemisphere fold, |V_us| differing between the
toolkit and the reference, and a c*tau rounded to four figures. So the pins are
asserted, not trusted.

If one of these fails, decide which side is wrong before editing: the prompt
defines the question the agent is answering, and truth.json is the answer.
"""
import json
import pytest
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROMPT = REPO / "benchmarks/llp_forward/variants/bare/prompts/user.md"
REFDIR = REPO / "benchmarks/llp_forward/soln/reference"
sys.path.insert(0, str(REPO / "benchmarks/llp_forward/soln/depr"))
sys.path.insert(0, str(REPO / "benchmarks/llp_forward/soln/code"))


def _text():
    return PROMPT.read_text()


def _truth():
    p = REFDIR / "out/truth_a.json"
    if not p.is_file():
        p = REPO / "benchmarks/llp_forward/soln/truth.json"
    return json.loads(p.read_text())


def test_geometry_pins_match_the_reference():
    """The apparatus in the prompt is the geometry the reference integrates."""
    DV = pytest.importorskip("derivation", reason="needs soln/depr/derivation.py, which is not distributed")
    t = _text()
    g = DV.GEOM
    for val, label in ((g["z_min_m"], "decay volume z_min"),
                       (g["z_max_m"], "decay volume z_max"),
                       (g["z_det_m"], "detector plane z"),
                       (g["z_prod_m"], "shielding start z_shield")):
        assert f"{val:g}" in t, f"{label} = {val} not stated in the prompt"
    # both radii are 0.92 and appear as such
    assert f"{g['r_volume_m']:g}" in t, "volume radius missing"
    assert f"{g['r_det_m']:g}" in t, "detector radius missing"
    # on-axis: x_off is zero, and the prompt says so in words instead
    assert g["x_off_m"] == 0.0, "prompt says on-axis but geometry is offset"
    assert "on-axis" in t
    print("[OK] geometry pins match derivation.GEOM")


def test_normalisation_pins_match_the_reference():
    import numpy as np
    t = _text()
    truth = _truth()
    assert truth["n_int"] == 2.7e18
    assert "2.7\\times10^{18}" in t, "N_int not stated"
    assert float(truth["n_target"]) == 3.0
    assert "\\geq3" in t, "the N_sig >= 3 rule is not stated"
    import ast
    if not (REFDIR / "flux/parent_flux_a.npz").is_file():
        pytest.skip("needs the reference flux sample, which is not distributed")
    raw = np.load(REFDIR / "flux/parent_flux_a.npz",
                  allow_pickle=True)["_meta"].item()
    # _meta is stored as a repr string, not a dict
    meta = raw if isinstance(raw, dict) else ast.literal_eval(str(raw))
    assert meta["sigma_inel_mb"] == 80.0
    assert "80.0" in t, "sigma_inel not stated"
    assert meta["sqrt_s_gev"] == 13600.0
    assert "13.6" in t, "sqrt(s) not stated"
    assert meta["theta_max_rad"] == 0.05
    assert "0.05" in t, "theta_max not stated"
    assert "Monash" in meta["tune"] and "Monash" in t, "tune not pinned"
    print("[OK] N_int, N*, sigma_inel, sqrt(s), theta_max, tune all pinned")


def test_mass_grid_matches_the_reference():
    """Compare NUMERICALLY: the prompt may write 0.70 where truth says 0.7."""
    t = _text()
    truth = _truth()
    line = next(l for l in t.splitlines() if "0.06" in l and "2.30" in l)
    stated = sorted(float(x) for x in re.findall(r"\d+\.\d+", line))
    assert stated == sorted(truth["grid_m_gev"]), (stated,
                                                   truth["grid_m_gev"])
    print(f"[OK] all {len(stated)} declared masses stated, values match")


def test_probe_points_match_the_reference():
    t = _text()
    truth = _truth()
    wp, gg = truth["width_probe"], truth["width_gg_probe"]
    ct = truth["ctau_probe"]
    assert wp["m_phi"] == 0.30 and wp["g"] == 4.2e-4
    assert gg["m_phi"] == 0.12 and gg["g"] == 1.0e-3
    assert ct["m_phi"] == 0.30 and list(ct["g"]) == [3.7e-6, 1.11e-5]
    for s in ("4.2\\times10^{-4}", "1.0\\times10^{-3}",
              "3.7\\times10^{-6}", "1.11\\times10^{-5}"):
        assert s in t, f"probe coupling {s} not stated"
    print("[OK] all four probe points match truth")


def test_sandbox_is_the_output_contract_only():
    """Interface scaffolding constant and complete; nothing else shipped."""
    sb = REPO / "benchmarks/llp_forward/variants/bare/sandbox/template"
    files = sorted(p.relative_to(sb).as_posix()
                   for p in sb.rglob("*") if p.is_file())
    assert files == ["results/answer_schema.json"], files
    schema = json.loads((sb / "results/answer_schema.json").read_text())
    t = _text()
    # The prompt points at the schema rather than repeating its field names,
    # except for the probe fields, which it tabulates explicitly.
    assert "results/answer_schema.json" in t, "prompt must point at the schema"
    for key in ("width_probe_gev", "width_gg_probe_gev", "ctau_probe_m"):
        assert key in schema.get("required", []), key
        assert key in t, f"probe field {key} not tabulated in the prompt"
    assert "dimuon-width formula" in t, "the formula deliverable is not asked for"
    print(f"[OK] sandbox ships only the schema; it is referenced and every "
          f"probe field is tabulated")


def test_withheld_material_is_actually_withheld():
    """The prompt must not leak what the variant claims to withhold."""
    t = _text().lower()
    for banned, why in (
            ("p_dec", "the decay-probability prescription"),
            ("exp(-l1", "the decay-probability prescription"),
            ("midpoint", "the acceptance convention"),
            ("beta*gamma", "the lab decay-length prescription"),
            ("j/psi", "the parent enumeration"),
            ("psi(2s)", "the parent enumeration"),
            ("kappa", "the reduced branching fraction"),
            ("b_hat", "the reduced branching fraction")):
        assert banned not in t, f"prompt leaks {why} ({banned!r})"
    # naming the parents individually would give away the enumeration
    for parent in (" d_s ", "d_s meson"):
        assert parent not in t, "prompt names a specific charm parent"
    print("[OK] no prescriptions or parent names leaked")


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("\nall bare-prompt pin tests passed")
