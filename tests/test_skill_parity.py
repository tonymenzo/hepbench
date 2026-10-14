"""The benchmark's skill copy must match the toolkit's canonical one.

`benchmarks/llp_forward/skills/pythia_forward_run_cards.md` is a copy of
heptapod's `skills/pythia_forward_run_cards/SKILL.md`. The duplication is
deliberate and is explained in `loadouts/tools_defined.yaml`: toolbase surfaces
toolkit skills globally (via `tb connect`, into ~/.claude/skills/) which would
leak into the core_only arm, while toolbench materialises a loadout's `skills:`
per trial, which is what a graded ablation needs. Two mechanisms, no bridge, so
the benchmark holds its own copy.

A copy drifts. This asserts it has not, against whichever heptapod version the
loadout pins -- so the guide the tools arm actually reads is the guide the
toolkit actually ships.

Skips rather than fails when the pinned toolkit is not installed on this
machine: the parity claim is unverifiable then, and a red test for a missing
optional dependency trains people to ignore it.
"""
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
BENCH = REPO / "benchmarks/llp_forward"
COPY = BENCH / "skills/pythia_forward_run_cards.md"
LOADOUT = BENCH / "loadouts/tools_defined.yaml"
TB_LOADOUT = REPO / ".toolbase/loadouts/forward-llp-defined.yaml"
CACHE = Path.home() / ".toolbase/cache/heptapod"


def _pinned_version():
    """The heptapod version the benchmark's toolbase loadout pins."""
    data = yaml.safe_load(TB_LOADOUT.read_text())
    return str((data.get("versions") or {}).get("heptapod", "")).strip()


def test_loadout_declares_the_skill():
    """tools_defined must actually deliver the guide, with a resolvable file."""
    data = yaml.safe_load(LOADOUT.read_text())
    skills = data.get("skills") or []
    assert skills, "tools_defined declares no skills; the tools arm gets no guide"
    entry = next(s for s in skills if s["name"] == "pythia_forward_run_cards")
    # toolbench resolves `file:` relative to the benchmark dir.
    assert (BENCH / entry["file"]).is_file(), entry["file"]
    assert entry.get("mode", "on_demand") in ("on_demand", "inline")
    print(f"[OK] tools_defined delivers {entry['name']} ({entry.get('mode')})")


def test_copy_matches_the_installed_toolkit():
    version = _pinned_version()
    assert version, "forward-llp-defined pins no heptapod version"
    src = CACHE / version / "skills/pythia_forward_run_cards/SKILL.md"
    if not src.is_file():
        pytest.skip(f"heptapod {version} not installed at {src}")
    assert COPY.read_text() == src.read_text(), (
        f"benchmark skill copy has drifted from heptapod {version}; "
        f"re-copy from {src}")
    print(f"[OK] skill copy identical to heptapod {version}")


def test_skill_is_self_contained():
    """toolbench copies ONE file, so the guide must not depend on siblings.

    heptapod ships the run cards as real files in cards/ next to the guide;
    those do not travel through the loadout mechanism, so the cards are inlined
    and this asserts they still are.
    """
    text = COPY.read_text()
    body = text.split("## 8. Starting-point run cards")[-1]
    cards = re.findall(r"```\n(.*?)```", body, re.S)
    assert len(cards) >= 2, f"expected the run cards inlined, found {len(cards)}"
    for card in cards:
        assert "Beams:eCM" in card and "SoftQCD" in card
    print(f"[OK] {len(cards)} run cards inlined; guide is self-contained")


def test_frontmatter_scopes_the_skill_to_a_declared_bundle():
    """The toolbase copy is bundle-scoped; an undeclared bundle gates it out."""
    version = _pinned_version()
    src = CACHE / version / "skills/pythia_forward_run_cards/SKILL.md"
    if not src.is_file():
        pytest.skip(f"heptapod {version} not installed")
    fm = yaml.safe_load(src.read_text().split("---")[1])
    assert fm.get("bundle") == "llp", fm.get("bundle")
    tk = yaml.safe_load((CACHE / version / "toolkit.yaml").read_text())
    assert fm["bundle"] in (tk.get("bundles") or {}), (
        f"skill scoped to bundle {fm['bundle']!r}, which the toolkit does not "
        f"declare -- toolbase would gate it out")
    print(f"[OK] skill scoped to declared bundle {fm['bundle']!r}")


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("\nall skill-parity tests passed")
