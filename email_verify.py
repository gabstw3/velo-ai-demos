#!/usr/bin/env python3
"""
email_verify.py — Pre-flight SMTP verification for Velo AI outreach

Verifies whether an email address can receive mail BEFORE building demos and drafting.
Runs a two-stage probe: catch-all detection first, then the real address.

Status codes:
  VERIFIED      — SMTP probe accepted RCPT TO (mailbox almost certainly exists)
  MX_ONLY       — Domain has MX records but individual mailbox can't be confirmed
                  (catch-all domain, Gmail, O365, Mimecast — proceed with personal-name addrs only)
  UNVERIFIABLE  — Couldn't reach the mail server (port 25 blocked, timeout, etc.)
  DEAD          — No MX records, or server hard-rejected the address (5xx)
  INVALID       — Malformed email syntax

Usage:
  python email_verify.py joel@joelgrosspa.com
  python email_verify.py --csv export.csv --col contact_email
  python email_verify.py --csv export.csv --col contact_email --out verified.csv
"""

import sys
import smtplib
import socket
import argparse
import csv
import time
import subprocess
from dataclasses import dataclass
from typing import Optional

PROBE_SENDER = "noreply@getveloai.co"
SMTP_TIMEOUT  = 8   # seconds per connection
BETWEEN_DELAY = 1.2 # seconds between checks (be polite to mail servers)

# Generic aliases that bounce even when the domain's MX is live
GENERIC_ALIASES = {
    # Universal
    "info", "contact", "hello", "support", "admin", "office",
    "mail", "team", "management", "managment", "reservations",
    # Dental / medical practice aliases
    "smile", "dental", "connect", "care", "health",
    # Catch-all functional aliases
    "emailus", "email", "inquiries", "inquiry", "booking", "bookings",
    "appointments", "reception", "front", "frontdesk", "desk",
    "general", "clinic", "practice",
    # Hospitality / restaurant
    "events", "catering", "dine", "dining",
    # Salon / beauty
    "beauty", "salon", "spa", "studio",
}

# Hosts that block SMTP probing or are catch-all by design
UNVERIFIABLE_HOSTS = [
    "google", "gmail", "googlemail",
    "outlook", "microsoft", "hotmail",
    "mimecast", "proofpoint", "barracuda",
    "pphosted", "ppe-hosted", "protection.outlook",
    "secureserver",   # GoDaddy — blocks probing
]

# @gmail.com and @googlemail.com addresses ARE verifiable (Google accepts RCPT TO probes for them).
# Custom domains using Google Workspace (aspmx.l.google.com MX) are NOT — individual mailboxes
# cannot be confirmed and guessed formats (firstname@domain.com) WILL hard-bounce.
GMAIL_NATIVE_DOMAINS = {"gmail.com", "googlemail.com"}

def is_google_workspace(domain: str, mx_host: str) -> bool:
    """Return True if a CUSTOM domain routes through Google Workspace (not @gmail.com itself)."""
    return (
        domain.lower() not in GMAIL_NATIVE_DOMAINS
        and ("aspmx" in mx_host.lower() or "googlemail" in mx_host.lower()
             or (mx_host.lower().endswith(".google.com") and "aspmx" in mx_host.lower()))
    )


@dataclass
class VerifyResult:
    email:            str
    domain:           str
    mx_host:          str
    status:           str          # VERIFIED | MX_ONLY | UNVERIFIABLE | DEAD | INVALID
    smtp_code:        Optional[int]
    note:             str
    safe_to_draft:    bool         # False for DEAD/INVALID/GOOGLE_WORKSPACE; True otherwise
    risky:            bool         # True when MX_ONLY + generic alias (info@, contact@, etc.)
    google_workspace: bool         # True when custom domain routes through Google MX — NEVER guess formats


# ── DNS helpers ────────────────────────────────────────────────────────────────

def resolve_mx(domain: str) -> Optional[str]:
    """Return highest-priority MX hostname for domain, or None if domain has no mail."""
    try:
        import dns.resolver
        records = dns.resolver.resolve(domain, "MX", lifetime=5)
        records = sorted(records, key=lambda r: r.preference)
        return str(records[0].exchange).rstrip(".")
    except ImportError:
        pass
    except Exception:
        return None

    # Fallback: dig (always available on macOS)
    try:
        out = subprocess.run(
            ["dig", "+short", "MX", domain],
            capture_output=True, text=True, timeout=5
        ).stdout.strip().splitlines()
        parsed = []
        for line in out:
            parts = line.split()
            if len(parts) == 2:
                try:
                    parsed.append((int(parts[0]), parts[1].rstrip(".")))
                except ValueError:
                    pass
        if parsed:
            parsed.sort(key=lambda x: x[0])
            return parsed[0][1]
    except Exception:
        pass

    return None


def is_unverifiable_host(mx_host: str) -> bool:
    return any(p in mx_host.lower() for p in UNVERIFIABLE_HOSTS)


# ── SMTP probe ─────────────────────────────────────────────────────────────────

def _rcpt_check(email: str, mx_host: str) -> tuple[Optional[int], str]:
    """
    Open an SMTP connection to mx_host:25 and issue RCPT TO <email>.
    Returns (smtp_code_or_None, message_string).
    Does NOT send any mail — issues QUIT after RCPT TO.
    """
    try:
        with smtplib.SMTP(timeout=SMTP_TIMEOUT) as s:
            s.connect(mx_host, 25)
            s.ehlo("getveloai.co")
            code, _ = s.mail(PROBE_SENDER)
            if code != 250:
                s.quit()
                return None, f"MAIL FROM rejected ({code})"
            code, msg = s.rcpt(email)
            s.quit()
            msg_str = msg.decode("utf-8", errors="ignore") if isinstance(msg, bytes) else str(msg)
            return code, msg_str[:140]
    except smtplib.SMTPServerDisconnected:
        return None, "Server closed connection early (probe-blocking)"
    except smtplib.SMTPConnectError as e:
        return None, f"SMTP connect error: {e}"
    except ConnectionRefusedError:
        return None, "Port 25 refused — likely blocked by ISP or firewall"
    except socket.timeout:
        return None, f"Timeout ({SMTP_TIMEOUT}s) reaching {mx_host}:25"
    except OSError as e:
        return None, f"Network error: {e}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def smtp_probe(email: str, mx_host: str) -> tuple[str, Optional[int], str]:
    """
    Two-stage probe:
      Stage 1 — test a known-fake address to detect catch-all domains.
      Stage 2 — test the real address (only if stage 1 rejected the fake).
    Returns (status, smtp_code, note).
    """
    domain = email.split("@")[1]

    # Skip hosts that block probing
    if is_unverifiable_host(mx_host):
        return "MX_ONLY", None, f"{mx_host} blocks SMTP probing — can't verify individual mailbox"

    # Stage 1: catch-all detection
    fake = f"velo_noexist_xyz999@{domain}"
    fake_code, fake_msg = _rcpt_check(fake, mx_host)

    if fake_code is None:
        # Can't connect at all — port 25 blocked or server unreachable
        return "UNVERIFIABLE", None, fake_msg

    if fake_code == 250:
        # Server accepted a nonsense address → catch-all
        return "MX_ONLY", fake_code, f"Catch-all domain — accepts any address, can't verify {email}"

    if fake_code in (550, 551, 552, 553, 554):
        # Good: server rejects unknown addresses → probe the real one
        real_code, real_msg = _rcpt_check(email, mx_host)
        if real_code is None:
            return "UNVERIFIABLE", None, f"Could not re-connect for {email}: {real_msg}"
        if real_code == 250:
            return "VERIFIED", real_code, f"Mailbox confirmed by {mx_host}"
        elif real_code in (550, 551, 552, 553, 554):
            return "DEAD", real_code, f"Mailbox rejected: {real_code} {real_msg}"
        else:
            return "MX_ONLY", real_code, f"Ambiguous response {real_code}: {real_msg}"

    # Temp rejection or other
    return "MX_ONLY", fake_code, f"Temporary/ambiguous server response: {fake_code} {fake_msg}"


# ── Main verify function ───────────────────────────────────────────────────────

def verify_email(email: str) -> VerifyResult:
    email = email.strip()

    # Syntax
    if "@" not in email:
        return VerifyResult(email, "", "", "INVALID", None, "Missing @ sign", False, False, False)
    parts = email.split("@")
    if len(parts) != 2 or not parts[0] or not parts[1] or "." not in parts[1]:
        return VerifyResult(email, "", "", "INVALID", None, "Invalid email syntax", False, False, False)

    local, domain = parts[0].lower(), parts[1].lower()

    # MX lookup
    mx_host = resolve_mx(domain)
    if not mx_host:
        return VerifyResult(
            email, domain, "", "DEAD", None,
            f"No MX records for {domain} — domain cannot receive email",
            False, False, False
        )

    # SMTP probe
    status, code, note = smtp_probe(email, mx_host)

    # Detect Google Workspace custom domains — individual mailboxes cannot be probed.
    # Guessing firstname@theirdomain.com WILL hard-bounce. Mark NOT safe to draft.
    google_ws = is_google_workspace(domain, mx_host)

    # Flag risky combos: MX_ONLY + generic alias — these must NOT be drafted
    is_generic = local in GENERIC_ALIASES
    risky = (status == "MX_ONLY") and is_generic

    # UNVERIFIABLE = treat as skip — too risky to guess
    # GOOGLE_WORKSPACE custom domain = NOT safe unless email was FOUND from external source
    if google_ws and status == "MX_ONLY":
        note = (f"GOOGLE WORKSPACE custom domain — individual mailboxes CANNOT be verified. "
                f"Only draft if this exact email was found on website/LinkedIn/ZoomInfo. "
                f"NEVER draft a guessed format (firstname@, lastname@, etc.).")
        safe_to_draft = False
    elif risky:
        note = f"{note} — generic alias, high bounce risk, DO NOT DRAFT"
        safe_to_draft = False
    elif status == "UNVERIFIABLE":
        note = f"{note} — port 25 blocked, cannot confirm; SKIP to avoid bounce risk"
        safe_to_draft = False
    else:
        safe_to_draft = status in ("VERIFIED", "MX_ONLY")

    return VerifyResult(email, domain, mx_host, status, code, note, safe_to_draft, risky, google_ws)


# ── Output helpers ─────────────────────────────────────────────────────────────

STATUS_ICON  = {"VERIFIED": "✓", "MX_ONLY": "~", "UNVERIFIABLE": "?", "DEAD": "✗", "INVALID": "✗"}
STATUS_COLOR = {
    "VERIFIED":     "\033[92m",  # green
    "MX_ONLY":      "\033[93m",  # yellow
    "UNVERIFIABLE": "\033[93m",  # yellow
    "DEAD":         "\033[91m",  # red
    "INVALID":      "\033[91m",  # red
}
RESET = "\033[0m"


def print_result(r: VerifyResult, verbose: bool = True):
    icon  = STATUS_ICON.get(r.status, "?")
    color = STATUS_COLOR.get(r.status, "")
    gws_tag = " [GOOGLE-WORKSPACE]" if r.google_workspace else ""
    tag   = f"[{r.status}]" + (" [RISKY-ALIAS]" if r.risky else "") + gws_tag
    print(f"{color}{icon} {tag:40}{RESET}  {r.email}")
    if verbose:
        if r.mx_host:
            print(f"    MX:            {r.mx_host}")
        print(f"    Note:          {r.note}")
        print(f"    Safe to draft: {'YES' if r.safe_to_draft else 'NO -- SKIP'}")
        if r.google_workspace:
            print(f"    🚫 GOOGLE WORKSPACE: Email must be FOUND (website/LinkedIn/ZoomInfo) — never guess format")
        if r.risky:
            print(f"    ⚠  Generic alias on unverifiable host — HIGH bounce risk")


# ── CSV batch mode ─────────────────────────────────────────────────────────────

def verify_csv_file(csv_path: str, col: str, out_path: Optional[str], delay: float):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if col not in fieldnames:
            print(f"ERROR: Column '{col}' not found. Available columns: {', '.join(fieldnames)}")
            sys.exit(1)
        for row in reader:
            rows.append(row)

    print(f"\nPre-flight check: {len(rows)} address(es) from '{col}' in {csv_path}\n")
    print("─" * 72)

    results: list[tuple[dict, VerifyResult]] = []
    for row in rows:
        email = row.get(col, "").strip()
        if not email:
            continue
        sys.stdout.write(f"  Checking {email:<45} ")
        sys.stdout.flush()
        r = verify_email(email)
        icon  = STATUS_ICON.get(r.status, "?")
        color = STATUS_COLOR.get(r.status, "")
        tag   = r.status + (" [RISKY]" if r.risky else "")
        print(f"{color}{icon} {tag}{RESET}")
        results.append((row, r))
        time.sleep(delay)

    # Summary
    by_status = {s: [] for s in ["VERIFIED", "MX_ONLY", "UNVERIFIABLE", "DEAD", "INVALID"]}
    risky_list = []
    for _, r in results:
        by_status.get(r.status, by_status["UNVERIFIABLE"]).append(r)
        if r.risky:
            risky_list.append(r)

    print(f"\n{'═' * 72}")
    print("SUMMARY")
    print(f"{'─' * 72}")
    print(f"  ✓ VERIFIED:      {len(by_status['VERIFIED']):3d}  — green light, send")
    print(f"  ~ MX_ONLY:       {len(by_status['MX_ONLY']):3d}  — domain live, mailbox unconfirmable")
    print(f"  ? UNVERIFIABLE:  {len(by_status['UNVERIFIABLE']):3d}  — couldn't probe (port 25 blocked?)")
    print(f"  ✗ DEAD:          {len(by_status['DEAD']):3d}  — NO MX or mailbox hard-rejected — SKIP")
    print(f"  ✗ INVALID:       {len(by_status['INVALID']):3d}  — bad syntax — SKIP")
    if risky_list:
        print(f"\n  ⚠  RISKY (MX_ONLY + generic alias — high bounce probability):")
        for r in risky_list:
            print(f"     {r.email}  →  {r.note}")

    dead_and_invalid = by_status["DEAD"] + by_status["INVALID"]
    if dead_and_invalid:
        print(f"\n  DO NOT DRAFT (DEAD / INVALID):")
        for r in dead_and_invalid:
            print(f"     ✗ {r.email}  →  {r.note}")

    # Write output CSV
    if out_path:
        new_fields = fieldnames + ["verify_status", "verify_mx", "verify_note",
                                   "safe_to_draft", "risky_alias"]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=new_fields)
            writer.writeheader()
            for row, r in results:
                row["verify_status"]  = r.status
                row["verify_mx"]      = r.mx_host
                row["verify_note"]    = r.note
                row["safe_to_draft"]  = "YES" if r.safe_to_draft else "NO"
                row["risky_alias"]    = "YES" if r.risky else "NO"
                writer.writerow(row)
        print(f"\n  Output → {out_path}")

    print()
    return results


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Velo AI pre-flight email verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python email_verify.py joel@joelgrosspa.com
  python email_verify.py --csv export.csv --col contact_email
  python email_verify.py --csv export.csv --col contact_email --out verified.csv
        """
    )
    parser.add_argument("email", nargs="?", help="Single email address to verify")
    parser.add_argument("--csv",   help="CSV file to batch-verify")
    parser.add_argument("--col",   default="contact_email",
                        help="CSV column containing emails (default: contact_email)")
    parser.add_argument("--out",   help="Output CSV path with verify_status columns added")
    parser.add_argument("--delay", type=float, default=BETWEEN_DELAY,
                        help=f"Seconds between checks in batch mode (default: {BETWEEN_DELAY})")
    args = parser.parse_args()

    if args.email:
        print(f"\nVerifying: {args.email}\n")
        r = verify_email(args.email)
        print_result(r, verbose=True)
        sys.exit(0 if r.safe_to_draft else 1)
    elif args.csv:
        verify_csv_file(args.csv, args.col, args.out, args.delay)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
