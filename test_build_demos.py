#!/usr/bin/env python3
"""
Tests for the demo build scripts (build_demo.py + build_recovery_demos.py).

The business risk these guard against is **brand leakage**: a generated,
personalized demo that still contains the source template's brand (e.g.
"Dr. Onyski" / "Wayside" / "Lance Ragland") — or an unrendered "@@marker@@" —
shipped to a prospect. The scripts already *print* warnings about this; these
tests turn the invariants into hard failures so a bad template/config change
can't slip through silently.

All assertions run against the real template files in the repo, using the
scripts' pure `transform()` functions (no files are written).

Run with:  pytest test_build_demos.py -v
"""
import re

import pytest

import build_demo as bd
import build_recovery_demos as br


# ──────────────────────────────────────────────────────────────────────────────
# build_demo.py — pure substitution primitives
# ──────────────────────────────────────────────────────────────────────────────

class TestRender:
    def test_substitutes_known_keys(self):
        out = bd.render("Hello @@name@@ from @@city@@", {"name": "Ada", "city": "NYC"})
        assert out == "Hello Ada from NYC"

    def test_leaves_unknown_markers_untouched(self):
        out = bd.render("@@known@@ and @@unknown@@", {"known": "X"})
        assert out == "X and @@unknown@@"

    def test_no_markers_is_identity(self):
        assert bd.render("plain text", {"a": "b"}) == "plain text"


# ──────────────────────────────────────────────────────────────────────────────
# build_demo.py — config + template integrity (the brand-leak guards)
# ──────────────────────────────────────────────────────────────────────────────

# Keys actually referenced by the substitution templates.
REFERENCED_KEYS = set(re.findall(r"@@(\w+)@@", " ".join(n for _, n in bd.SIMPLE_SUBS)))


class TestBuildDemoConfigs:
    def test_referenced_keys_were_discovered(self):
        # Guard against the regex silently matching nothing.
        assert REFERENCED_KEYS

    @pytest.mark.parametrize("slug", list(bd.CONFIGS))
    def test_config_supplies_every_referenced_key(self, slug):
        missing = REFERENCED_KEYS - set(bd.CONFIGS[slug])
        assert not missing, f"{slug} config is missing keys: {sorted(missing)}"

    @pytest.mark.parametrize("slug", list(bd.CONFIGS))
    def test_no_unrendered_markers(self, slug):
        out = bd.transform(bd.TEMPLATE.read_text(), bd.CONFIGS[slug])
        assert "@@" not in out, f"{slug} demo still contains @@ markers"

    @pytest.mark.parametrize("slug", list(bd.CONFIGS))
    def test_no_source_brand_leak(self, slug):
        out = bd.transform(bd.TEMPLATE.read_text(), bd.CONFIGS[slug])
        assert "Onyski" not in out, f"{slug} demo leaks source doctor 'Onyski'"
        assert "Wayside" not in out, f"{slug} demo leaks source brand 'Wayside'"

    @pytest.mark.parametrize("slug", list(bd.CONFIGS))
    def test_practice_name_is_present(self, slug):
        out = bd.transform(bd.TEMPLATE.read_text(), bd.CONFIGS[slug])
        assert bd.CONFIGS[slug]["practice_name"] in out

    def test_simple_subs_match_template_exactly_once(self):
        # Every `old` string should appear exactly once in the source template;
        # zero means a stale sub, more than one means an ambiguous replace.
        template = bd.TEMPLATE.read_text()
        bad = {old[:50]: template.count(old) for old, _ in bd.SIMPLE_SUBS
               if template.count(old) != 1}
        assert not bad, f"subs not matching exactly once: {bad}"


# ──────────────────────────────────────────────────────────────────────────────
# build_recovery_demos.py — pure substitution primitives
# ──────────────────────────────────────────────────────────────────────────────

class TestApplySubs:
    def test_applies_in_order(self):
        # Later subs operate on the result of earlier ones.
        out = br.apply_subs("A", [("A", "B"), ("B", "C")])
        assert out == "C"

    def test_multiple_distinct_replacements(self):
        out = br.apply_subs("Lance at Ragland", [("Lance", "Glenn"), ("Ragland", "Klausman")])
        assert out == "Glenn at Klausman"

    def test_transform_applies_cleanup_after_subs(self):
        out = br.transform("Lance", [("Lance", "Jennifer")], [("Jennifer", "Kathy")])
        assert out == "Kathy"

    def test_transform_without_cleanup(self):
        assert br.transform("x", [("x", "y")]) == "y"


# ──────────────────────────────────────────────────────────────────────────────
# build_recovery_demos.py — JOBS registry integrity + brand-leak regression
# ──────────────────────────────────────────────────────────────────────────────

class TestJobsRegistry:
    def test_jobs_is_non_empty(self):
        assert br.JOBS

    @pytest.mark.parametrize("job", br.JOBS, ids=[j[0] for j in br.JOBS])
    def test_job_shape(self, job):
        assert len(job) >= 3, "each job needs (slug, base, subs[, cleanup])"
        slug, base, subs = job[0], job[1], job[2]
        assert isinstance(slug, str) and slug
        assert isinstance(subs, list)

    @pytest.mark.parametrize("job", br.JOBS, ids=[j[0] for j in br.JOBS])
    def test_base_template_exists(self, job):
        base = job[1]
        assert (br.ROOT / base).exists(), f"base template {base} not found"

    def test_slugs_are_unique(self):
        slugs = [j[0] for j in br.JOBS]
        dupes = {s for s in slugs if slugs.count(s) > 1}
        assert not dupes, f"duplicate job slugs: {dupes}"


class TestBrandLeakRegression:
    """The core guard: regenerating any job from its real base template must not
    leave the source brand behind, nor any unrendered @@ marker."""

    @pytest.mark.parametrize("job", br.JOBS, ids=[j[0] for j in br.JOBS])
    def test_no_source_brand_leak(self, job):
        slug, base, subs = job[0], job[1], job[2]
        cleanup = job[3] if len(job) > 3 else None
        out = br.transform((br.ROOT / base).read_text(), subs, cleanup)
        brand = br.SOURCE_BRAND.get(base)
        if brand:
            assert brand not in out, f"{slug} leaks source brand '{brand}' from {base}"

    @pytest.mark.parametrize("job", br.JOBS, ids=[j[0] for j in br.JOBS])
    def test_no_unrendered_markers(self, job):
        slug, base, subs = job[0], job[1], job[2]
        cleanup = job[3] if len(job) > 3 else None
        out = br.transform((br.ROOT / base).read_text(), subs, cleanup)
        assert "@@" not in out, f"{slug} demo still contains @@ markers"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
