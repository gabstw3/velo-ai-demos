#!/usr/bin/env python3
"""Generate a new demo HTML from the Wayside template by applying substitutions."""
import sys
from pathlib import Path

TEMPLATE = Path(__file__).parent / "wayside.html"

# === Config per prospect ===
CONFIGS = {
    "smiletown": {
        # Identity
        "practice_name": "Your Smile Town Dental",
        "doctor_full": "Dr. Karan Doomra, DDS",
        "doctor_last": "Dr. Doomra",
        "concierge_name": "Smile Town Concierge",
        "est": "Est. 2019",
        "address_line1": "1177 Rinehart Road",
        "address_line2": "Sanford, FL 32771",
        "phone": "(407) 504-1992",
        "hours_short": "Tue–Fri 8a–5p · Sat 9a–5p",
        "booking_icon": "S",
        "short_brand": "Smile Town",  # standalone uses of "Wayside"
        "pronoun_subj": "he",        # he/she
        "pronoun_obj": "him",        # him/her
        "pronoun_poss": "his",       # his/her
        "since_both": "since he graduated from NYU",  # replaces "since 2010"
        "welcoming_phrase": "has been welcoming new patients to Smile Town since 2019",
        "promise_text": "Dr. Doomra and Dr. Tella are on call to respond to their patients' needs as soon as possible. As a patient of Smile Town, you're never alone.",
    },
    "lakeforest": {
        "practice_name": "Lake Forest Family Dentistry",
        "doctor_full": "Dr. Dennis Horanic, DDS",
        "doctor_last": "Dr. Horanic",
        "concierge_name": "Lake Forest Concierge",
        "est": "Est. 1993",
        "address_line1": "5300 W. State Road 46, Suite 1000",
        "address_line2": "Sanford, FL 32771",
        "phone": "(407) 328-9398",
        "hours_short": "Mon–Thu 8a–5p · Fri 8a–3p",
        "booking_icon": "L",
        "short_brand": "Lake Forest",
        "pronoun_subj": "he",
        "pronoun_obj": "him",
        "pronoun_poss": "his",
        "since_both": "since 1993",
        "welcoming_phrase": "has been welcoming new patients to Lake Forest since 1993",
        "promise_text": "Dr. Horanic is on call to respond to his patients' needs as soon as possible. As a patient of Lake Forest, you're never alone.",
    },
}

# Base substitutions derived from Wayside template
# Each entry: (old_exact_string, key_from_config)
SIMPLE_SUBS = [
    # Title tag
    ("Wayside Family Dental — After-Hours Concierge | Powered by Velo AI",
     "@@practice_name@@ — After-Hours Concierge | Powered by Velo AI"),
    # Demo banner alert
    ("This is a live demo built by Velo AI for Wayside Family Dental.",
     "This is a live demo built by Velo AI for @@practice_name@@."),
    # Practice mark
    ("Sanford, Florida · Est. 2012", "Sanford, Florida · @@est@@"),
    # Practice name h1
    ("<h1 class=\"practice-name\">Wayside Family Dental</h1>",
     "<h1 class=\"practice-name\">@@practice_name@@</h1>"),
    # Doctor paragraph
    ("<p class=\"practice-doctor\">Dr. Lyudmila A. Onyski, DDS</p>",
     "<p class=\"practice-doctor\">@@doctor_full@@</p>"),
    # Promise card
    ("Dr. Onyski is on call to respond to her patients' needs as soon as possible. As a patient of Wayside, you're never alone.",
     "@@promise_text@@"),
    # Address line 1
    ("4907 International Pkwy, Suite 1041<br>Sanford, FL 32771",
     "@@address_line1@@<br>@@address_line2@@"),
    # Phone in sidebar
    ("<div>(407) 732-4570</div>", "<div>@@phone@@</div>"),
    # Hours short
    ("Mon–Thu 8a–5p · Fri 8a–1p", "@@hours_short@@"),
    # Status text
    ("<strong>Wayside Concierge</strong> · Available 24/7",
     "<strong>@@concierge_name@@</strong> · Available 24/7"),
    # Input hint
    ("A patient of Wayside? Dr. Onyski will be notified immediately for urgent matters.",
     "A patient of @@short_brand@@? @@doctor_last@@ will be notified immediately for urgent matters."),
    # Bot messages — main conversation
    ("Good evening — you've reached the after-hours line for Wayside Family Dental. Dr. Onyski is unavailable right now, but I can help with most things and reach her directly if it's urgent.",
     "Good evening — you've reached the after-hours line for @@practice_name@@. @@doctor_last@@ is unavailable right now, but I can help with most things and reach @@pronoun_obj@@ directly if it's urgent."),
    # Emergency empathy line
    ("I'm sorry you're dealing with this — dental pain at this hour is genuinely awful, and you did the right thing reaching out. Let me get you to Dr. Onyski as quickly as possible.",
     "I'm sorry you're dealing with this — dental pain at this hour is genuinely awful, and you did the right thing reaching out. Let me get you to @@doctor_last@@ as quickly as possible."),
    # Severe urgency handoff
    ("Understood. I'm flagging this as urgent and texting Dr. Onyski now — she'll call you back within 15 minutes.<br><br>While we wait, can I get your first name and best callback number? If swelling spreads to your eye, jaw, or neck, please go to the ER immediately — that's the one thing that can't wait.",
     "Understood. I'm flagging this as urgent and texting @@doctor_last@@ now — @@pronoun_subj@@'ll call you back within 15 minutes.<br><br>While we wait, can I get your first name and best callback number? If swelling spreads to your eye, jaw, or neck, please go to the ER immediately — that's the one thing that can't wait."),
    # Mild/moderate handoff
    ("Got it. Dr. Onyski will want to see you first thing — she keeps emergency slots open every morning at 8 AM specifically for situations like this.<br><br>What's your first name? I'll have her office pre-confirm with you by 7:30 AM.",
     "Got it. @@doctor_last@@ will want to see you first thing — @@pronoun_subj@@ keeps emergency slots open every morning at 8 AM specifically for situations like this.<br><br>What's your first name? I'll have @@pronoun_poss@@ office pre-confirm with you by 7:30 AM."),
    # High-value path
    ("Great choice to reach out — both implants and Invisalign are major decisions and Dr. Onyski has been doing both since 2010, so you're in capable hands.<br><br>Which one were you curious about?",
     "Great choice to reach out — both implants and Invisalign are major decisions and @@doctor_last@@ has been doing both @@since_both@@, so you're in capable hands.<br><br>Which one were you curious about?"),
    # Consult pitch
    ("Both are best answered with a 30-minute consult — Dr. Onyski does a digital scan, reviews your options, and gives you a treatment plan with real numbers before you commit to anything. Wayside also accepts CareCredit if financing helps.<br><br>Want me to hold a consult slot for you this week?",
     "Both are best answered with a 30-minute consult — @@doctor_last@@ does a digital scan, reviews your options, and gives you a treatment plan with real numbers before you commit to anything. @@short_brand@@ also accepts CareCredit if financing helps.<br><br>Want me to hold a consult slot for you this week?"),
    # Booking path
    ("Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Dr. Onyski's schedule?",
     "Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on @@doctor_last@@'s schedule?"),
    # New patient welcome
    ("Welcome — Dr. Onyski has been welcoming new patients to Wayside since 2012, and most of our patients come from referrals, so it's nice when someone finds us directly.<br><br>What's your first name?",
     "Welcome — @@doctor_last@@ @@welcoming_phrase@@, and most of our patients come from referrals, so it's nice when someone finds us directly.<br><br>What's your first name?"),
    # Question path
    ("Of course — go ahead and type your question and I'll do my best. If it's something Dr. Onyski needs to weigh in on personally, I'll route it to her and she'll get back to you in the morning.",
     "Of course — go ahead and type your question and I'll do my best. If it's something @@doctor_last@@ needs to weigh in on personally, I'll route it to @@pronoun_obj@@ and @@pronoun_subj@@'ll get back to you in the morning."),
    # Name collection responses
    ("Thank you, ${memory.name}. What's the best phone number to reach you at? I want to make sure Dr. Onyski has it before tomorrow morning.",
     "Thank you, ${memory.name}. What's the best phone number to reach you at? I want to make sure @@doctor_last@@ has it before tomorrow morning."),
    ("Thanks, ${memory.name}. What's the best phone number? Dr. Onyski's office will text you a confirmation within an hour of opening.",
     "Thanks, ${memory.name}. What's the best phone number? @@doctor_last@@'s office will text you a confirmation within an hour of opening."),
    ("Thank you, ${memory.name}. What's the best callback number? Dr. Onyski will call you within 15 minutes.",
     "Thank you, ${memory.name}. What's the best callback number? @@doctor_last@@ will call you within 15 minutes."),
    # Paging confirmation
    ("Got it, ${memory.name} — I just paged Dr. Onyski. Expect a call from <strong>(407) 732-4570</strong> within 15 minutes.<br><br>Stay calm, sit upright if possible, and avoid hot or cold liquids until she calls. You're going to be okay.",
     "Got it, ${memory.name} — I just paged @@doctor_last@@. Expect a call from <strong>@@phone@@</strong> within 15 minutes.<br><br>Stay calm, sit upright if possible, and avoid hot or cold liquids until @@pronoun_subj@@ calls. You're going to be okay."),
    # All set confirmation
    ("All set, ${memory.name}. Dr. Onyski's office will call (${text}) by 7:30 AM to confirm your appointment.<br><br>Anything else I can help with tonight?",
     "All set, ${memory.name}. @@doctor_last@@'s office will call (${text}) by 7:30 AM to confirm your appointment.<br><br>Anything else I can help with tonight?"),
    # New patient reason
    ("Got it. Dr. Onyski opens new-patient slots Tuesday through Thursday — would tomorrow at 10:30 AM or Wednesday at 2 PM work better for you?",
     "Got it. @@doctor_last@@ opens new-patient slots Tuesday through Thursday — would tomorrow at 10:30 AM or Wednesday at 2 PM work better for you?"),
    # Question fallback
    ("Thanks for sending that over. I've logged your question for Dr. Onyski to review first thing in the morning — she or someone from her team will reach out by 10 AM.<br><br>Want me to also hold a consult slot in case you'd like to discuss it in person?",
     "Thanks for sending that over. I've logged your question for @@doctor_last@@ to review first thing in the morning — @@pronoun_subj@@ or someone from @@pronoun_poss@@ team will reach out by 10 AM.<br><br>Want me to also hold a consult slot in case you'd like to discuss it in person?"),
    # Booking card fields
    ("<span class=\"value\">Dr. Lyudmila A. Onyski</span>",
     "<span class=\"value\">@@doctor_full@@</span>"),
    ("<span class=\"value\">4907 International Pkwy, Suite 1041</span>",
     "<span class=\"value\">@@address_line1@@</span>"),
    # Booking icon
    ("<div class=\"booking-icon\">W</div>", "<div class=\"booking-icon\">@@booking_icon@@</div>"),
    # Booking confirmation
    ("You're all set, ${memory.name}. Dr. Onyski has been notified, and you'll get a confirmation text from <strong>(407) 732-4570</strong> within the hour.<br><br>Have a good night — and thank you for choosing Wayside.",
     "You're all set, ${memory.name}. @@doctor_last@@ has been notified, and you'll get a confirmation text from <strong>@@phone@@</strong> within the hour.<br><br>Have a good night — and thank you for choosing @@short_brand@@."),
    # Alternative time proposal
    ("No problem. Dr. Onyski has openings tomorrow at 8 AM, 11:30 AM, or 4:15 PM — which works best?",
     "No problem. @@doctor_last@@ has openings tomorrow at 8 AM, 11:30 AM, or 4:15 PM — which works best?"),
    # Booking hold intro
    ("Perfect. Here's the hold I'm creating for Dr. Onyski:",
     "Perfect. Here's the hold I'm creating for @@doctor_last@@:"),
    # JS msg-meta
    ("<div class=\"msg msg-bot\">${text}</div><div class=\"msg-meta\">Wayside Concierge</div>",
     "<div class=\"msg msg-bot\">${text}</div><div class=\"msg-meta\">@@concierge_name@@</div>"),
]


def render(template_str: str, config: dict) -> str:
    out = template_str
    for k, v in config.items():
        out = out.replace(f"@@{k}@@", v)
    return out


def build(slug: str, config: dict) -> None:
    template = TEMPLATE.read_text()
    out = template
    for old, new_template in SIMPLE_SUBS:
        new = render(new_template, config)
        count = out.count(old)
        if count == 0:
            print(f"  ! NOT FOUND: {old[:60]!r}")
        elif count > 1:
            print(f"  ! MULTIPLE ({count}) instances of: {old[:60]!r}")
        out = out.replace(old, new)
    # Sanity: any @@ markers left means we missed a key
    leftovers = [line for line in out.split("\n") if "@@" in line]
    if leftovers:
        print(f"  ! {len(leftovers)} lines still contain @@ markers")
        for ln in leftovers[:5]:
            print(f"    {ln.strip()[:100]}")
    target = TEMPLATE.parent / f"{slug}.html"
    target.write_text(out)
    print(f"Wrote {target} ({len(out)} bytes)")


if __name__ == "__main__":
    slugs = sys.argv[1:] if len(sys.argv) > 1 else list(CONFIGS.keys())
    for slug in slugs:
        print(f"\n=== {slug} ===")
        build(slug, CONFIGS[slug])
