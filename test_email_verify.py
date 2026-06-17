#!/usr/bin/env python3
"""
Unit tests for email_verify.py

Focus: the pure decision logic that gates whether a cold-outreach address is
`safe_to_draft`. A wrong verdict means a bounce (and damage to sending-domain
reputation), so these branches are the highest-value thing in the repo to lock
down. Network-touching code (DNS + SMTP) is mocked so the suite is fast,
deterministic, and runnable offline.

Run with:  pytest test_email_verify.py -v
"""
from unittest import mock

import pytest

import email_verify as ev


# ──────────────────────────────────────────────────────────────────────────────
# Syntax validation  (verify_email → INVALID, no network involved)
# ──────────────────────────────────────────────────────────────────────────────

class TestSyntaxValidation:
    @pytest.mark.parametrize("bad", [
        "noatsign.com",          # missing @
        "two@@ats.com",          # split() yields 3 parts
        "a@b@c.com",             # multiple @
        "@nolocal.com",          # empty local part
        "nodomain@",             # empty domain
        "noTLD@localhost",       # no dot in domain
        "",                      # empty string
    ])
    def test_invalid_syntax_is_flagged(self, bad):
        r = ev.verify_email(bad)
        assert r.status == "INVALID"
        assert r.safe_to_draft is False

    def test_invalid_does_not_touch_network(self):
        # Syntax check must short-circuit before any DNS/SMTP work.
        with mock.patch.object(ev, "resolve_mx") as m_mx:
            ev.verify_email("garbage")
            m_mx.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# Google Workspace detection  (pure string logic, high-stakes carve-outs)
# ──────────────────────────────────────────────────────────────────────────────

class TestIsGoogleWorkspace:
    @pytest.mark.parametrize("domain,mx,expected", [
        # Native Gmail is verifiable → must NOT be treated as Workspace.
        ("gmail.com", "gmail-smtp-in.l.google.com", False),
        ("googlemail.com", "gmail-smtp-in.l.google.com", False),
        # Custom domains routed through Google MX → Workspace (cannot probe mailbox).
        ("acmedental.com", "aspmx.l.google.com", True),
        ("acmedental.com", "alt1.aspmx.l.google.com", True),
        ("acmedental.com", "ASPMX.L.GOOGLE.COM", True),       # case-insensitive
        ("acmedental.com", "googlemail-x.example.com", True), # 'googlemail' token
        # Non-Google hosts → not Workspace.
        ("acmedental.com", "mail.acmedental.com", False),
        ("acmedental.com", "mx1.secureserver.net", False),
    ])
    def test_classification(self, domain, mx, expected):
        assert ev.is_google_workspace(domain, mx) is expected


# ──────────────────────────────────────────────────────────────────────────────
# Probe-blocking host detection
# ──────────────────────────────────────────────────────────────────────────────

class TestIsUnverifiableHost:
    @pytest.mark.parametrize("mx,expected", [
        ("aspmx.l.google.com", True),          # contains 'google'
        ("mx.outlook.com", True),
        ("us-smtp-inbound-1.mimecast.com", True),
        ("mx1.secureserver.net", True),        # GoDaddy
        ("mail.acmedental.com", False),
        ("mx.privateemail.com", False),
    ])
    def test_detection(self, mx, expected):
        assert ev.is_unverifiable_host(mx) is expected


# ──────────────────────────────────────────────────────────────────────────────
# Two-stage SMTP probe  (mock _rcpt_check so no real connections are made)
# ──────────────────────────────────────────────────────────────────────────────

class TestSmtpProbe:
    def test_probe_blocking_host_short_circuits_to_mx_only(self):
        # Should never even attempt an _rcpt_check for known-blocking hosts.
        with mock.patch.object(ev, "_rcpt_check") as m:
            status, code, _ = ev.smtp_probe("x@acme.com", "aspmx.l.google.com")
            assert status == "MX_ONLY"
            assert code is None
            m.assert_not_called()

    def test_unreachable_server_is_unverifiable(self):
        # Stage 1 can't connect → UNVERIFIABLE.
        with mock.patch.object(ev, "_rcpt_check", return_value=(None, "timeout")):
            status, _, _ = ev.smtp_probe("x@acme.com", "mail.acme.com")
            assert status == "UNVERIFIABLE"

    def test_catch_all_domain_is_mx_only(self):
        # Stage 1 fake address ACCEPTED (250) → catch-all → MX_ONLY.
        with mock.patch.object(ev, "_rcpt_check", return_value=(250, "ok")):
            status, code, _ = ev.smtp_probe("real@acme.com", "mail.acme.com")
            assert status == "MX_ONLY"
            assert code == 250

    def test_real_mailbox_confirmed_is_verified(self):
        # Stage 1 rejects fake (550), Stage 2 accepts real (250) → VERIFIED.
        responses = iter([(550, "no such user"), (250, "ok")])
        with mock.patch.object(ev, "_rcpt_check", side_effect=lambda *a: next(responses)):
            status, code, _ = ev.smtp_probe("real@acme.com", "mail.acme.com")
            assert status == "VERIFIED"
            assert code == 250

    def test_real_mailbox_rejected_is_dead(self):
        responses = iter([(550, "no such user"), (550, "no such user")])
        with mock.patch.object(ev, "_rcpt_check", side_effect=lambda *a: next(responses)):
            status, _, _ = ev.smtp_probe("ghost@acme.com", "mail.acme.com")
            assert status == "DEAD"

    def test_ambiguous_real_response_is_mx_only(self):
        responses = iter([(550, "no such user"), (450, "greylisted")])
        with mock.patch.object(ev, "_rcpt_check", side_effect=lambda *a: next(responses)):
            status, _, _ = ev.smtp_probe("real@acme.com", "mail.acme.com")
            assert status == "MX_ONLY"

    def test_temp_rejection_on_stage1_is_mx_only(self):
        with mock.patch.object(ev, "_rcpt_check", return_value=(450, "try later")):
            status, _, _ = ev.smtp_probe("real@acme.com", "mail.acme.com")
            assert status == "MX_ONLY"


# ──────────────────────────────────────────────────────────────────────────────
# verify_email end-to-end decision logic
# (mock resolve_mx + smtp_probe so we test only the branching/safe_to_draft rules)
# ──────────────────────────────────────────────────────────────────────────────

class TestVerifyEmailDecisions:
    def test_no_mx_is_dead(self):
        with mock.patch.object(ev, "resolve_mx", return_value=None):
            r = ev.verify_email("someone@no-mail-domain.com")
            assert r.status == "DEAD"
            assert r.safe_to_draft is False

    def test_verified_is_safe(self):
        with mock.patch.object(ev, "resolve_mx", return_value="mail.acme.com"), \
             mock.patch.object(ev, "smtp_probe", return_value=("VERIFIED", 250, "ok")):
            r = ev.verify_email("jane@acme.com")
            assert r.status == "VERIFIED"
            assert r.safe_to_draft is True
            assert r.risky is False

    def test_mx_only_personal_address_is_safe(self):
        with mock.patch.object(ev, "resolve_mx", return_value="mail.acme.com"), \
             mock.patch.object(ev, "smtp_probe", return_value=("MX_ONLY", None, "catch-all")):
            r = ev.verify_email("jane.doe@acme.com")
            assert r.safe_to_draft is True
            assert r.risky is False

    def test_mx_only_generic_alias_is_risky_and_unsafe(self):
        # info@ on a catch-all domain → must NOT be drafted.
        with mock.patch.object(ev, "resolve_mx", return_value="mail.acme.com"), \
             mock.patch.object(ev, "smtp_probe", return_value=("MX_ONLY", None, "catch-all")):
            r = ev.verify_email("info@acme.com")
            assert r.risky is True
            assert r.safe_to_draft is False

    def test_unverifiable_is_unsafe(self):
        with mock.patch.object(ev, "resolve_mx", return_value="mail.acme.com"), \
             mock.patch.object(ev, "smtp_probe", return_value=("UNVERIFIABLE", None, "port 25 blocked")):
            r = ev.verify_email("jane@acme.com")
            assert r.safe_to_draft is False

    def test_dead_mailbox_is_unsafe(self):
        with mock.patch.object(ev, "resolve_mx", return_value="mail.acme.com"), \
             mock.patch.object(ev, "smtp_probe", return_value=("DEAD", 550, "rejected")):
            r = ev.verify_email("ghost@acme.com")
            assert r.safe_to_draft is False

    def test_google_workspace_custom_domain_never_safe(self):
        # Custom domain on Google MX + MX_ONLY → guessed formats hard-bounce.
        with mock.patch.object(ev, "resolve_mx", return_value="aspmx.l.google.com"), \
             mock.patch.object(ev, "smtp_probe", return_value=("MX_ONLY", None, "blocks probing")):
            r = ev.verify_email("jane@acmedental.com")
            assert r.google_workspace is True
            assert r.safe_to_draft is False
            assert "GOOGLE WORKSPACE" in r.note

    def test_native_gmail_can_be_verified_and_safe(self):
        # @gmail.com itself is verifiable and not flagged as Workspace.
        with mock.patch.object(ev, "resolve_mx", return_value="gmail-smtp-in.l.google.com"), \
             mock.patch.object(ev, "smtp_probe", return_value=("VERIFIED", 250, "ok")):
            r = ev.verify_email("someone@gmail.com")
            assert r.google_workspace is False
            assert r.safe_to_draft is True

    def test_email_is_stripped_and_lowercased(self):
        with mock.patch.object(ev, "resolve_mx", return_value="mail.acme.com") as m_mx, \
             mock.patch.object(ev, "smtp_probe", return_value=("VERIFIED", 250, "ok")):
            r = ev.verify_email("  Jane@ACME.com  ")
            # domain passed to resolve_mx must be normalized lower-case.
            m_mx.assert_called_once_with("acme.com")
            assert r.domain == "acme.com"


# ──────────────────────────────────────────────────────────────────────────────
# Output lookup tables stay in sync with the documented status set
# ──────────────────────────────────────────────────────────────────────────────

class TestStatusMaps:
    STATUSES = {"VERIFIED", "MX_ONLY", "UNVERIFIABLE", "DEAD", "INVALID"}

    def test_every_status_has_an_icon(self):
        assert self.STATUSES <= set(ev.STATUS_ICON)

    def test_every_status_has_a_color(self):
        assert self.STATUSES <= set(ev.STATUS_COLOR)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
