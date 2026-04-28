#!/usr/bin/env python3
"""
RECOVERY GENERATOR — Build 11 custom demos to fix the bad sends.

For each prospect, takes the closest base template and applies thorough
substitutions:
  - business identity (name, owner, address, phone, hours, est)
  - sector-specific chips (replaces dental/probate/buy-sell defaults)
  - bot greeting + voice
  - conversation route adaptations (where needed)
  - booking card details
  - color palette tweaks where industry warrants

All output files go to /Users/g/velo-ai-demos/<slug>.html
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent

# ============================================================================
# Helper: per-prospect heavy substitution
# ============================================================================

def apply_subs(text: str, subs: list) -> str:
    """Apply ordered list of (old, new) replacements."""
    for old, new in subs:
        text = text.replace(old, new)
    return text


# ============================================================================
# PROSPECT CONFIGS — full per-prospect substitution maps
# Each config includes (a) the base template to use and (b) a list of (old, new) pairs
# ============================================================================

# ----------------------------------------------------------------------------
# KLAUSMAN LAW — PI/insurance/workers' comp, Winter Park
# Base: ragland.html (estate planning)
# ----------------------------------------------------------------------------
KLAUSMAN_SUBS = [
    # Title / banner / branding
    ("Lance A. Ragland, P.A. — After-Hours Intake | Powered by Velo AI",
     "Klausman Law — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Lance A. Ragland, P.A.",
     "This is a live demo built by Velo AI for Klausman Law"),
    ("Winter Springs, Florida · Est. 2015", "Winter Park, Florida · Est. 1998"),
    ('<h1 class="practice-name">Lance A. Ragland, P.A.</h1>',
     '<h1 class="practice-name">Klausman Law</h1>'),
    ('<p class="practice-doctor">Lance A. Ragland, Esq.</p>',
     '<p class="practice-doctor">Glenn Klausman, Esq.</p>'),
    # Promise
    ("<h4>Available When You Need Him</h4>",
     "<h4>The Calls That Matter Most</h4>"),
    ("Estate matters rarely surface during business hours. Lance is committed to being there for clients during life's most difficult transitions. You're never alone.",
     "Accidents and insurance disputes don't wait for business hours. Glenn is committed to being the first call you can actually reach — and the last call you'll need to make."),
    # Address / phone / hours
    ("5750 Canton Cove<br>Winter Springs, FL 32708",
     "1101 N Lakemont Ave, Suite 200<br>Winter Park, FL 32792"),
    ("(407) 960-6069", "(407) 917-1718"),
    ("By Appointment · Mon–Fri 9a–5p", "Mon–Fri 9a–5p · Free Consultation"),
    # Status / branding
    ("Intake powered by", "Intake powered by"),
    ("<strong>Ragland Intake</strong> · Available 24/7",
     "<strong>Klausman Intake</strong> · Available 24/7"),
    ("A current client of Lance's? He'll be notified directly for urgent matters.",
     "Already a client? Glenn will be notified directly for urgent matters on your case."),
    # Bot greeting + chips — replace probate/planning with PI/insurance
    ("Good evening — you've reached the after-hours line for the Law Offices of Lance A. Ragland. Lance focuses entirely on estate planning, probate, and trust matters. He's unavailable right now, but I can take down what's on your mind and get him to reach back out.",
     "Good evening — you've reached the after-hours line for Klausman Law. Glenn handles personal injury and insurance disputes — accident cases, denied claims, and workers' comp. He's not available right this minute, but I can take down what happened and get him on a call with you fast."),
    # Chip set replacement
    ("{ label: '🕯️ I lost a loved one', value: 'probate' },\n        { label: '📜 Plan a will or trust', value: 'planning' },\n        { label: '🏥 Power of attorney / healthcare', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }",
     "{ label: '🚑 Recent accident or injury', value: 'accident' },\n        { label: '⚖️ Insurance denied my claim', value: 'insurance' },\n        { label: '💼 Workers\\' comp question', value: 'comp' },\n        { label: '❓ A general question', value: 'question' }"),
    # Label map
    ("'probate': \"I lost a loved one and need probate help\",\n      'planning': \"I'd like to plan a will or trust\",\n      'poa': \"I need a power of attorney or healthcare paperwork\"",
     "'accident': \"I was recently in an accident or got injured\",\n      'insurance': \"My insurance company denied my claim\",\n      'comp': \"I have a workers' comp question\""),
    # Probate route → accident route
    ("if (value === 'probate') {\n      memory.matter = 'probate';\n      await addBotMessage(\n        `I'm so sorry for your loss. Please take whatever time you need.<br><br>Lance has guided families through probate for nearly thirty years, and most of what feels overwhelming right now has a clear path forward. The two things that help him move quickly when he calls you back: who passed, and whether they had a will.`,",
     "if (value === 'accident') {\n      memory.matter = 'accident';\n      await addBotMessage(\n        `I'm sorry you're dealing with this — accidents leave you with pain, paperwork, and pressure all at once. Glenn has handled thousands of injury cases in 27 years and the first thing he usually does is take that pressure off you so you can focus on healing. Two things help him move fast when he calls back: when did the accident happen, and have you talked to any insurance adjusters yet.`,"),
    ("`If you're able to share — who is this for?`,\n        900,\n        [\n          { label: 'Spouse', value: 'spouse' },\n          { label: 'Parent', value: 'parent' },\n          { label: 'Other family member', value: 'other-family' }\n        ]",
     "`First — when did the accident happen?`,\n        900,\n        [\n          { label: 'Today / yesterday', value: 'today' },\n          { label: 'Within the last week', value: 'week' },\n          { label: 'A while ago', value: 'older' }\n        ]"),
    ("'spouse': \"My spouse\",\n      'parent': \"A parent\",\n      'other-family': \"Another family member\"",
     "'today': \"Today or yesterday\",\n      'week': \"Within the last week\",\n      'older': \"It's been a while\""),
    ("if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.relation = value;\n      await addBotMessage(\n        `Thank you. Did they have a will or any estate documents in place?`,\n        900,\n        [\n          { label: 'Yes, they had a will', value: 'has-will' },\n          { label: 'No', value: 'no-will' },\n          { label: \"I'm not sure\", value: 'unsure-will' }\n        ]\n      );\n      return;\n    }",
     "if (['today', 'week', 'older'].includes(value)) {\n      memory.timing = value;\n      await addBotMessage(\n        `Got it. Have you spoken with the at-fault driver's insurance company yet?`,\n        900,\n        [\n          { label: 'No, not yet', value: 'no-insurance' },\n          { label: 'Yes — they called me', value: 'yes-insurance' },\n          { label: 'They denied me', value: 'denied-insurance' }\n        ]\n      );\n      return;\n    }"),
    ("['has-will', 'no-will', 'unsure-will'].includes(value)",
     "['no-insurance', 'yes-insurance', 'denied-insurance'].includes(value)"),
    ("memory.hasWill = value;\n      await addBotMessage(\n        `Got it. One more question, then I'll get this in front of Lance — is anything time-pressured? Sometimes accounts get frozen, or a property has a deadline. Other times there's just no rush.`,",
     "memory.insuranceContact = value;\n      await addBotMessage(\n        `Got it. One more question, then I'll get this in front of Glenn — are you currently in pain or did you have to go to the ER? That changes how fast he wants to get back to you.`,"),
    ("'urgent-frozen': \"Yes — accounts are frozen / property at risk\",\n      'urgent-soon': \"Soon, but not in crisis\",\n      'urgent-planning': \"No urgency — just planning ahead\"",
     "'urgent-frozen': \"Yes — ER visit / ongoing pain\",\n      'urgent-soon': \"Some pain but managing\",\n      'urgent-planning': \"No injuries, just need legal help\""),
    ("[\n          { label: '🔴 Yes — accounts frozen / property at risk', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not in crisis', value: 'urgent-soon' },\n          { label: '🟢 No urgency — just planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Yes — ER visit or ongoing pain', value: 'urgent-frozen' },\n          { label: '🟡 Some pain but managing', value: 'urgent-soon' },\n          { label: '🟢 Not injured, just need legal help', value: 'urgent-planning' }\n        ]"),
    # Severe path
    ("`Understood — that's exactly the kind of thing Lance wants to know about right away. I'm flagging this as priority and Lance will call you first thing tomorrow morning, before his appointments start.<br><br>Can I get your first name and best callback number? If a deadline is in the next 48 hours, please mention it.`",
     "`Understood — Glenn wants to hear from you ASAP if you're hurt. I'm flagging this as priority and he'll call you within the hour during business hours, or first thing in the morning if it's late tonight.<br><br>Can I get your first name and best callback number? If you're at a hospital, please mention it.`"),
    # Soft path
    ("`Thank you — that helps. Lance opens his calendar Tuesday through Thursday for new probate matters and sets aside ninety minutes per consultation so nothing feels rushed.<br><br>What's your first name? I'll have him reach out by mid-morning to set a time that works.`",
     "`Thank you — that helps. Glenn offers free consultations for injury cases — no fee unless he wins your case. He'll review the situation, walk you through what your case might be worth, and explain the timeline so you know what to expect.<br><br>What's your first name? I'll have him reach out tomorrow to set up the call.`"),
    # Planning path → insurance dispute path
    ("if (value === 'planning') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart of you to think about this — most people put off estate planning for years and regret the procrastination. Lance has been doing wills, trusts, and estate plans exclusively since 2015, so this is exactly his bread and butter.<br><br>Most clients in your shoes are weighing one of two things: <em>\"Do I just need a will, or do I need a trust?\"</em> and <em>\"What's this going to cost me?\"</em><br><br>Both are answered properly in a one-hour consult — Lance reviews your situation, walks you through the difference, and gives you a flat-fee quote before you commit to anything. Want me to hold a slot this week or next?`,",
     "if (value === 'insurance') {\n      memory.matter = 'insurance';\n      await addBotMessage(\n        `Insurance denials are exactly what Glenn handles every week. Insurance companies count on people accepting the first 'no' — they're often wrong, and a properly contested claim can flip outcome and dollar amount dramatically.<br><br>Most clients in your shoes are wondering: <em>\"Was the denial legitimate?\"</em> and <em>\"Is fighting it worth it?\"</em><br><br>Both are answered in a free consultation — Glenn reviews your denial letter and policy, tells you straight whether you have a case, and only takes it if he thinks you'll win. Want me to hold a slot this week?`,"),
    # POA path → workers' comp
    ("if (value === 'poa') {\n      memory.matter = 'poa';\n      await addBotMessage(\n        `These conversations are hard — usually they come up because someone in the family is going through a health change. Lance can put together a power of attorney and healthcare surrogate quickly, often within a few days if needed.<br><br>Just so I get the right urgency to him: is this for an immediate situation, or planning ahead?`,",
     "if (value === 'comp') {\n      memory.matter = 'comp';\n      await addBotMessage(\n        `Workers' comp can feel impossible to navigate — most claimants are dealing with HR pressure, doctors who work for the employer, and a system designed to deny first and pay last. Glenn has handled hundreds of these cases.<br><br>Just so I get the right urgency to him: are you currently off work, having benefits denied, or planning ahead?`,"),
    ("[\n          { label: '🔴 Immediate — health is declining', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not crisis', value: 'urgent-soon' },\n          { label: '🟢 Planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Off work / benefits denied', value: 'urgent-frozen' },\n          { label: '🟡 Working but in pain', value: 'urgent-soon' },\n          { label: '🟢 Just need legal advice', value: 'urgent-planning' }\n        ]"),
    # General question path
    ("`Of course — go ahead and type your question. If it's something Lance needs to weigh in on personally, I'll route it to him and he'll get back to you in the morning. If it's something I can answer from his practice info, I'll do my best.`",
     "`Of course — type your question. If it's something Glenn needs to weigh in on personally (case strategy, settlement evaluation, opposing counsel), I'll route it to him and he'll get back to you in the morning.`"),
    # Booking card icon + matter
    ('<div class="booking-icon">L</div>',
     '<div class="booking-icon">K</div>'),
    ('<span class="value">Lance A. Ragland, Esq.</span>',
     '<span class="value">Glenn Klausman, Esq.</span>'),
    ('<span class="value">5750 Canton Cove, Winter Springs</span>',
     '<span class="value">1101 N Lakemont Ave, Winter Park</span>'),
    # Matter map
    ("'planning': 'Estate Planning Consultation',\n          'poa': 'Power of Attorney Consultation',\n          'probate': 'Probate Consultation',\n          'question': 'General Consultation'",
     "'insurance': 'Insurance Dispute Consultation (Free)',\n          'comp': 'Workers Comp Consultation (Free)',\n          'accident': 'Accident Case Consultation (Free)',\n          'question': 'General Consultation (Free)'"),
    # Replace remaining Lance references with Glenn
    ("Lance has been notified", "Glenn has been notified"),
    ("Lance will reach out", "Glenn will reach out"),
    ("Lance opens new-patient slots Tuesday through Thursday",
     "Glenn opens his calendar Tuesday through Thursday for new cases"),
    ("`No problem. Lance has openings Tuesday at 11 AM, Wednesday at 3 PM, or Friday at 10 AM — which works best?`",
     "`No problem. Glenn has openings Tuesday at 11 AM, Wednesday at 3 PM, or Friday at 10 AM — which works best?`"),
    ("Tuesday at 11 AM, Wednesday at 3 PM, or Friday at 10 AM", "Tuesday at 11 AM, Wednesday at 3 PM, or Friday at 10 AM"),
    # Cleanup any remaining Lance, Ragland, debbie references
    ("Lance ", "Glenn "),
    ("Lance's", "Glenn's"),
    ("Lance.", "Glenn."),
    ("Lance,", "Glenn,"),
    ("his office (Debbie)", "his office"),
    # Replace 'Lance' standalone occurrences (above patterns may not have caught all)
    ("welcome from Lance", "welcome from Glenn"),
    # Stetson references etc
    ("(407) 960-6069", "(407) 917-1718"),  # in case missed earlier
]

# ----------------------------------------------------------------------------
# FRANK FAMILY LAW — Family/divorce/custody, Altamonte Springs
# Base: ragland.html
# ----------------------------------------------------------------------------
FRANK_SUBS = [
    ("Lance A. Ragland, P.A. — After-Hours Intake | Powered by Velo AI",
     "Frank Family Law Practice — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Lance A. Ragland, P.A.",
     "This is a live demo built by Velo AI for Frank Family Law Practice"),
    ("Winter Springs, Florida · Est. 2015", "Altamonte Springs, Florida · Est. 2009"),
    ('<h1 class="practice-name">Lance A. Ragland, P.A.</h1>',
     '<h1 class="practice-name">Frank Family Law</h1>'),
    ('<p class="practice-doctor">Lance A. Ragland, Esq.</p>',
     '<p class="practice-doctor">Jennifer Frank, Esq.</p>'),
    ("<h4>Available When You Need Him</h4>",
     "<h4>The Calls Families Need to Make</h4>"),
    ("Estate matters rarely surface during business hours. Lance is committed to being there for clients during life's most difficult transitions. You're never alone.",
     "Family decisions rarely happen on a 9-to-5 schedule. Jennifer is committed to being there for clients during the most personal transitions of their lives — divorce, custody, and everything in between."),
    ("5750 Canton Cove<br>Winter Springs, FL 32708",
     "999 Douglas Ave, Suite 3309<br>Altamonte Springs, FL 32714"),
    ("(407) 960-6069", "(407) 629-2208"),
    ("By Appointment · Mon–Fri 9a–5p", "Mon–Fri 9a–5p · Confidential consults"),
    ("<strong>Ragland Intake</strong> · Available 24/7",
     "<strong>Frank Family Intake</strong> · Available 24/7"),
    ("A current client of Lance's? He'll be notified directly for urgent matters.",
     "A current client? Jennifer will be notified directly for urgent matters."),
    # Bot greeting
    ("Good evening — you've reached the after-hours line for the Law Offices of Lance A. Ragland. Lance focuses entirely on estate planning, probate, and trust matters. He's unavailable right now, but I can take down what's on your mind and get him to reach back out.",
     "Good evening — you've reached the after-hours line for Frank Family Law. Jennifer practices exclusively in family law — divorce, custody, support, and parenting. She's unavailable right now, but everything you share with me is confidential. I'll take down what's on your mind and get her to reach back out."),
    # Chips
    ("{ label: '🕯️ I lost a loved one', value: 'probate' },\n        { label: '📜 Plan a will or trust', value: 'planning' },\n        { label: '🏥 Power of attorney / healthcare', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }",
     "{ label: '🚨 Custody emergency', value: 'custody' },\n        { label: '💔 Considering divorce', value: 'divorce' },\n        { label: '👶 Child support question', value: 'support' },\n        { label: '❓ A general question', value: 'question' }"),
    ("'probate': \"I lost a loved one and need probate help\",\n      'planning': \"I'd like to plan a will or trust\",\n      'poa': \"I need a power of attorney or healthcare paperwork\"",
     "'custody': \"I have a custody emergency\",\n      'divorce': \"I'm considering filing for divorce\",\n      'support': \"I have a child support question\""),
    # Probate → custody emergency
    ("if (value === 'probate') {\n      memory.matter = 'probate';\n      await addBotMessage(\n        `I'm so sorry for your loss. Please take whatever time you need.<br><br>Lance has guided families through probate for nearly thirty years, and most of what feels overwhelming right now has a clear path forward. The two things that help him move quickly when he calls you back: who passed, and whether they had a will.`,",
     "if (value === 'custody') {\n      memory.matter = 'custody';\n      await addBotMessage(\n        `I'm sorry you're dealing with this — custody crises usually mean someone you love is in a hard spot, and you're trying to protect them. Jennifer handles custody emergencies regularly. The two things that help her move fast: what's happening right now, and whether the kids are currently safe.`,"),
    ("`If you're able to share — who is this for?`,\n        900,\n        [\n          { label: 'Spouse', value: 'spouse' },\n          { label: 'Parent', value: 'parent' },\n          { label: 'Other family member', value: 'other-family' }\n        ]",
     "`If you're able to share — what's the situation?`,\n        900,\n        [\n          { label: 'Other parent took/keeping kids', value: 'spouse' },\n          { label: 'Safety concern with the children', value: 'parent' },\n          { label: 'Court order being violated', value: 'other-family' }\n        ]"),
    ("'spouse': \"My spouse\",\n      'parent': \"A parent\",\n      'other-family': \"Another family member\"",
     "'spouse': \"The other parent took the kids\",\n      'parent': \"Safety concern with the children\",\n      'other-family': \"Court order being violated\""),
    ("if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.relation = value;\n      await addBotMessage(\n        `Thank you. Did they have a will or any estate documents in place?`,\n        900,\n        [\n          { label: 'Yes, they had a will', value: 'has-will' },\n          { label: 'No', value: 'no-will' },\n          { label: \"I'm not sure\", value: 'unsure-will' }\n        ]\n      );\n      return;\n    }",
     "if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.situation = value;\n      await addBotMessage(\n        `Thank you. Are the children physically safe right now?`,\n        900,\n        [\n          { label: 'Yes, they\\'re safe', value: 'has-will' },\n          { label: \"I'm not sure\", value: 'no-will' },\n          { label: 'No — there\\'s immediate danger', value: 'unsure-will' }\n        ]\n      );\n      return;\n    }"),
    ("['has-will', 'no-will', 'unsure-will'].includes(value)",
     "['has-will', 'no-will', 'unsure-will'].includes(value)"),
    ("memory.hasWill = value;\n      await addBotMessage(\n        `Got it. One more question, then I'll get this in front of Lance — is anything time-pressured? Sometimes accounts get frozen, or a property has a deadline. Other times there's just no rush.`,",
     "memory.safety = value;\n      await addBotMessage(\n        `Got it. One more question, then I'll get this to Jennifer — is there an active court order in place, or are you in a stage before any orders exist?`,"),
    ("'urgent-frozen': \"Yes — accounts are frozen / property at risk\",\n      'urgent-soon': \"Soon, but not in crisis\",\n      'urgent-planning': \"No urgency — just planning ahead\"",
     "'urgent-frozen': \"Active order being violated\",\n      'urgent-soon': \"Order exists but situation changing\",\n      'urgent-planning': \"No order yet\""),
    ("[\n          { label: '🔴 Yes — accounts frozen / property at risk', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not in crisis', value: 'urgent-soon' },\n          { label: '🟢 No urgency — just planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Active order being violated', value: 'urgent-frozen' },\n          { label: '🟡 Order exists, situation changing', value: 'urgent-soon' },\n          { label: '🟢 No order yet — early stages', value: 'urgent-planning' }\n        ]"),
    ("`Understood — that's exactly the kind of thing Lance wants to know about right away. I'm flagging this as priority and Lance will call you first thing tomorrow morning, before his appointments start.<br><br>Can I get your first name and best callback number? If a deadline is in the next 48 hours, please mention it.`",
     "`Understood — Jennifer wants to hear from you tonight if there's an active violation. If the children are in immediate danger, please call 911 first. I'm flagging this as priority and Jennifer will call you within the hour during business hours, or first thing in the morning if it's late tonight.<br><br>Can I get your first name and best callback number?`"),
    ("`Thank you — that helps. Lance opens his calendar Tuesday through Thursday for new probate matters and sets aside ninety minutes per consultation so nothing feels rushed.<br><br>What's your first name? I'll have him reach out by mid-morning to set a time that works.`",
     "`Thank you — that helps. Jennifer keeps confidential consultation slots Tuesday through Thursday for new family law matters. She's been practicing family law exclusively for over 15 years.<br><br>What's your first name? I'll have her reach out tomorrow morning to set a time.`"),
    # Planning → divorce
    ("if (value === 'planning') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart of you to think about this — most people put off estate planning for years and regret the procrastination. Lance has been doing wills, trusts, and estate plans exclusively since 2015, so this is exactly his bread and butter.<br><br>Most clients in your shoes are weighing one of two things: <em>\"Do I just need a will, or do I need a trust?\"</em> and <em>\"What's this going to cost me?\"</em><br><br>Both are answered properly in a one-hour consult — Lance reviews your situation, walks you through the difference, and gives you a flat-fee quote before you commit to anything. Want me to hold a slot this week or next?`,",
     "if (value === 'divorce') {\n      memory.matter = 'divorce';\n      await addBotMessage(\n        `That's a hard place to be — and reaching out now means you're trying to do this thoughtfully instead of in crisis. Jennifer has been practicing family law for over 15 years and her first goal in any consult is to give you an honest read on what your situation actually looks like.<br><br>Most clients in your shoes are weighing two things: <em>\"Is this really happening?\"</em> and <em>\"What does it cost — financially and emotionally?\"</em><br><br>Both get answered in a confidential one-hour consult. Jennifer walks you through your options, your rights, and a realistic timeline before you make any decisions. Want me to hold a slot this week or next?`,"),
    # POA → child support
    ("if (value === 'poa') {\n      memory.matter = 'poa';\n      await addBotMessage(\n        `These conversations are hard — usually they come up because someone in the family is going through a health change. Lance can put together a power of attorney and healthcare surrogate quickly, often within a few days if needed.<br><br>Just so I get the right urgency to him: is this for an immediate situation, or planning ahead?`,",
     "if (value === 'support') {\n      memory.matter = 'support';\n      await addBotMessage(\n        `Child support questions usually come up at one of two moments — either you're paying or receiving and the amount feels wrong, or there's a change happening (job loss, custody shift, age milestone) that needs a modification. Jennifer can usually tell within a 30-minute call whether it's worth filing or whether the math actually works out.<br><br>Which situation is closer to yours?`,"),
    ("[\n          { label: '🔴 Immediate — health is declining', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not crisis', value: 'urgent-soon' },\n          { label: '🟢 Planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Major change happening now', value: 'urgent-frozen' },\n          { label: '🟡 Amount feels wrong', value: 'urgent-soon' },\n          { label: '🟢 Just need general info', value: 'urgent-planning' }\n        ]"),
    ("`Of course — go ahead and type your question. If it's something Lance needs to weigh in on personally, I'll route it to him and he'll get back to you in the morning. If it's something I can answer from his practice info, I'll do my best.`",
     "`Of course — type your question. If it's something Jennifer needs to weigh in on personally (strategy, opposing counsel, complex custody), I'll route it to her and she'll get back to you in the morning.`"),
    ('<div class="booking-icon">L</div>',
     '<div class="booking-icon">F</div>'),
    ('<span class="value">Lance A. Ragland, Esq.</span>',
     '<span class="value">Jennifer Frank, Esq.</span>'),
    ('<span class="value">5750 Canton Cove, Winter Springs</span>',
     '<span class="value">999 Douglas Ave, Altamonte Springs</span>'),
    ("'planning': 'Estate Planning Consultation',\n          'poa': 'Power of Attorney Consultation',\n          'probate': 'Probate Consultation',\n          'question': 'General Consultation'",
     "'divorce': 'Divorce Consultation',\n          'support': 'Child Support Consultation',\n          'custody': 'Custody Matter Consultation',\n          'question': 'General Consultation'"),
    ("(407) 960-6069", "(407) 629-2208"),
    # Lance → Jennifer pronoun + name swaps (do these LAST)
    ("Lance has been notified", "Jennifer has been notified"),
    ("Lance will reach out", "Jennifer will reach out"),
    ("`No problem. Lance has openings Tuesday at 11 AM, Wednesday at 3 PM, or Friday at 10 AM — which works best?`",
     "`No problem. Jennifer has openings Tuesday at 11 AM, Wednesday at 3 PM, or Friday at 10 AM — which works best?`"),
    ("Lance opens new-patient slots Tuesday through Thursday",
     "Jennifer opens her calendar Tuesday through Thursday for new family law matters"),
    # Pronouns: he → she, his → her, him → her
    # Apply via specific phrases instead of bulk to avoid breaking JS
    ("if it's late tonight.<br><br>Can I get your first name", "if it's late tonight.<br><br>Can I get your first name"),  # noop
    ("Lance ", "Jennifer "),
    ("Lance's", "Jennifer's"),
    ("Lance.", "Jennifer."),
    ("Lance,", "Jennifer,"),
    ("Lance:", "Jennifer:"),
    ("his office (Debbie)", "her office"),
    # general "he" "his" "him" pronoun fixes (in body text only — careful with JS keywords)
    (" before his appointments start", " before her appointments start"),
    (" set aside ninety minutes", " set aside ninety minutes"),  # noop
    (" he calls you back", " she calls you back"),
    (" he calls", " she calls"),
    (" he reach out", " she reach out"),
    (" reach back out", " reach back out"),  # noop
    (" his bread and butter", " her bread and butter"),
    (" he reviews your", " she reviews your"),
    (" he can put together", " she can put together"),
    (" he wants to know", " she wants to know"),
    (" he wants to hear", " she wants to hear"),
    (" he'll call you", " she'll call you"),
    (" he opens his calendar", " she opens her calendar"),
    (" he or his office", " she or her office"),
    ("he'll either reply directly or have his office", "she'll either reply directly or have her office"),
]

# ----------------------------------------------------------------------------
# SUNBRIGHT REALTY — Boutique RE, Lou Salvemini, Clermont
# Base: homelis.html
# ----------------------------------------------------------------------------
SUNBRIGHT_SUBS = [
    ("Homelis Realty — After-Hours Lead Qualifier | Powered by Velo AI",
     "Sunbright Realty — After-Hours Lead Qualifier | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Homelis Realty.",
     "This is a live demo built by Velo AI for Sunbright Realty."),
    ("Casselberry, Florida · Est. 2018", "Clermont, Florida · 16-Agent Boutique"),
    ('<h1 class="practice-name">Homelis Realty</h1>',
     '<h1 class="practice-name">Sunbright Realty</h1>'),
    ('<p class="practice-doctor">Warren Spencer, Broker/Owner</p>',
     '<p class="practice-doctor">Lou Salvemini Jr., Broker/Owner</p>'),
    ("<h4>Real Estate Doesn't Sleep</h4>",
     "<h4>16 Agents, One Number, Always Open</h4>"),
    ("The Saturday-night Zillow scroll, the Sunday open-house follow-up, the after-dinner pre-qualification — Warren is committed to capturing every lead. Even when he's at a closing.",
     "Whether it's a Saturday-night Zillow scroll or a Sunday open-house follow-up, Lou and the Sunbright team are committed to capturing every lead in real time — even when one of the 16 agents is mid-closing."),
    ("1490 Sunshadow Dr, Ste 2000<br>Casselberry, FL 32707",
     "1825 East Hwy 50, Suite 100<br>Clermont, FL 34711"),
    ("(407) 337-8333", "(352) 536-3714"),
    ("<strong>Homelis Concierge</strong> · Available 24/7",
     "<strong>Sunbright Concierge</strong> · Available 24/7"),
    ("Already working with Warren? He'll be notified directly for active deals.",
     "Already working with a Sunbright agent? They'll be notified directly for active deals."),
    # Greeting
    ("Welcome to Homelis Realty. I'm Warren's after-hours concierge — I can answer most questions, qualify what you're looking for, and get you on Warren's calendar so he can hit the ground running tomorrow.",
     "Welcome to Sunbright Realty. I'm the after-hours concierge for Lou and the team — I can answer most questions, qualify what you're looking for, and route you to the right agent. The Sunbright team handles Lake County, Clermont, Minneola, and Groveland markets."),
    # Buyer path tweaks
    ("Great — Warren and his team have closed over $50M in Central Florida sales. The market moves fast right now, so the more I can lock down tonight, the more aggressive Warren can be on Monday morning.",
     "Great — Sunbright is one of Lake County's most active boutique brokerages, with 16 agents covering Clermont, Minneola, Groveland, and the Four Corners. The market moves fast right now, so the more I can lock down tonight, the more aggressive your agent can be on Monday morning."),
    # First-time buyer / DPA pivot — Sunbright doesn't run a mortgage company, so soften
    ("Perfect — you may not know this, but Warren actually runs <strong>Homelis Mortgage</strong> alongside the brokerage (NMLS# 2702735). One conversation, one team, both sides handled. Most buyers save weeks doing it this way.",
     "Perfect — Sunbright works with several preferred local lenders who specialize in Florida buyers, including some who routinely close in under 30 days. Lou's team will introduce you to the right one based on your situation. Most buyers save weeks doing it this way."),
    # Just looking
    ("`No pressure at all — most of Warren's best clients started exactly here. He'll meet you where you are: zero-pressure 30-minute sit-down to map out neighborhoods, price ranges, and what pre-approval looks like when you're ready.<br><br>Want to lock that in this week or next?`",
     "`No pressure at all — most of Sunbright's best clients started exactly here. Lou or one of the 16 agents will meet you where you are: zero-pressure 30-minute sit-down to map out Lake County neighborhoods, price ranges, and what pre-approval looks like when you're ready.<br><br>Want to lock that in this week or next?`"),
    # Urgency lines
    ("Got it — Warren keeps Tuesday afternoons clear specifically for buyers who need to move fast.",
     "Got it — Lou keeps Tuesday afternoons clear specifically for buyers who need to move fast in the Lake County market."),
    ("Solid timeline — Warren's planning meetings are perfect for that horizon.",
     "Solid timeline — Sunbright's planning meetings are perfect for that horizon."),
    ("Smart to start early — gives Warren time to learn what you actually want, not just what the search filters say.",
     "Smart to start early — gives the Sunbright team time to learn what you actually want, not just what the search filters say."),
    # Seller pitch
    ("Warren's brokerage was ranked #1 in West Volusia for sold transactions in 2024 — so you're in good hands. The two questions every seller asks first: <em>\"What's it worth?\"</em> and <em>\"How fast can it move?\"</em><br><br>Both get answered properly in a 60-minute listing consultation at your home — Warren walks the property, pulls comps, and gives you a real strategy. Free, no obligation. What's your timeline?",
     "Sunbright is one of Lake County's most active brokerages — 16 agents who actually know the local micro-markets. The two questions every seller asks first: <em>\"What's it worth?\"</em> and <em>\"How fast can it move?\"</em><br><br>Both get answered properly in a 60-minute listing consultation at your home — your Sunbright agent walks the property, pulls comps, and gives you a real strategy. Free, no obligation. What's your timeline?"),
    # Listing visit lines
    ("Understood — life moves fast sometimes. Warren can be at your door this week with comps in hand.",
     "Understood — life moves fast sometimes. Your Sunbright agent can be at your door this week with comps in hand."),
    ("Perfect timeline — Warren can plan the staging and listing strategy properly with that runway.",
     "Perfect timeline — Sunbright can plan the staging and listing strategy properly with that runway."),
    ("Smart to know your number before deciding — Warren will give you an honest valuation, not a hype number.",
     "Smart to know your number before deciding — your Sunbright agent will give you an honest valuation, not a hype number."),
    # First-time / DPA path
    ("This is one of Warren's favorite conversations. He runs a <strong>Down Payment Assistance Center</strong> alongside the brokerage and has helped over a hundred first-time buyers in Central FL get into a home with way less down than they thought possible — sometimes $0 down for qualified buyers.",
     "First-time buyer programs in Lake County are bigger than most people realize — there are state and county programs that combine to make $0-down-on-paper deals possible for qualified buyers. Sunbright works with lenders who specialize in these. Lou personally walks first-time buyers through it."),
    # General question
    ("`Of course — type your question and I'll do my best. If it's something Warren needs to weigh in on personally (offer strategy, contract details, neighborhood specifics), I'll route it to him and he'll get back to you in the morning.`",
     "`Of course — type your question and I'll do my best. If it's something Lou or your assigned agent needs to weigh in on personally (offer strategy, contract details, Lake County specifics), I'll route it to them and someone will get back to you in the morning.`"),
    # Booking + confirmations
    ("Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Warren's calendar?",
     "Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Lou's calendar?"),
    ('<div class="booking-icon">H</div>', '<div class="booking-icon">S</div>'),
    ('<span class="value">Warren Spencer</span>', '<span class="value">Lou Salvemini Jr.</span>'),
    ('<span class="value">1490 Sunshadow Dr, Casselberry</span>',
     '<span class="value">1825 East Hwy 50, Clermont</span>'),
    # Phone confirms in chat lines
    ("`(407) 337-8333`", "`(352) 536-3714`"),
    ("Warren or his team will text a confirmation by 9 AM.",
     "Lou or your assigned agent will text a confirmation by 9 AM."),
    ("Warren wants to pull comps before he calls.",
     "The team wants to pull comps before the visit."),
    ("Warren will reach out", "Lou will reach out"),
    ("Warren has been notified", "Lou has been notified"),
    ("`No problem. Warren has openings Tuesday at 11 AM, Wednesday at 4 PM, or Friday at 9:30 AM — which works best?`",
     "`No problem. Lou has openings Tuesday at 11 AM, Wednesday at 4 PM, or Friday at 9:30 AM — which works best?`"),
    # Phone in confirm message
    ("(407) 337-8333", "(352) 536-3714"),
    # Page redirect references (homelis.com)
    ("homelisrealty.com", "sunbrightrealty.com"),
    ("Homelis Mortgage", "Sunbright preferred lenders"),
]

# ----------------------------------------------------------------------------
# GOLDIE SALON — Luxury hair salon, Lake Mary
# Base: wayside.html (heavy adaptation — dental → salon)
# ----------------------------------------------------------------------------
# This needs the most work. Will use a different approach.

# ============================================================================
# BUILD ROUTINE
# ============================================================================

def build(slug: str, base: str, subs: list, final_cleanup: list = None):
    base_path = ROOT / base
    out_path = ROOT / f"{slug}.html"
    text = base_path.read_text()
    text = apply_subs(text, subs)
    if final_cleanup:
        text = apply_subs(text, final_cleanup)
    out_path.write_text(text)

    # Sanity check
    source_brand = {"ragland.html": "Lance", "homelis.html": "Warren", "wayside.html": "Onyski"}.get(base, "")
    leaks = text.count(source_brand) if source_brand else 0
    print(f"  Wrote {out_path.name} ({len(text)} bytes, {leaks} '{source_brand}' leaks)")
    return out_path


# Final cleanup passes — catch any remaining brand leaks after prospect-specific subs
KLAUSMAN_CLEANUP = [
    ("Lance", "Glenn"),
    ("Ragland", "Klausman"),
]

FRANK_CLEANUP = [
    ("Lance", "Jennifer"),
    ("Ragland", "Frank"),
]

SUNBRIGHT_CLEANUP = [
    ("Warren Spencer", "Lou Salvemini Jr."),
    ("Warren", "Lou"),
    ("Homelis Realty", "Sunbright Realty"),
    ("Homelis", "Sunbright"),
    ("Casselberry", "Clermont"),  # in case missed
    ("Sunshadow Dr", "East Hwy 50"),
]

# ----------------------------------------------------------------------------
# GOLDIE SALON — Lake Mary luxury hair salon
# Base: wayside.html (dental → salon adaptation)
# ----------------------------------------------------------------------------
GOLDIE_SUBS = [
    # Identity
    ("Wayside Family Dental — After-Hours Concierge | Powered by Velo AI",
     "Goldie Salon — After-Hours Booking Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Wayside Family Dental.",
     "This is a live demo built by Velo AI for Goldie Salon."),
    ("Sanford, Florida · Est. 2012", "Lake Mary, Florida · Luxury Hair"),
    ('<h1 class="practice-name">Wayside Family Dental</h1>',
     '<h1 class="practice-name">Goldie Salon</h1>'),
    ('<p class="practice-doctor">Dr. Lyudmila A. Onyski, DDS</p>',
     '<p class="practice-doctor">The Goldie Team</p>'),
    ("<h4>The 24/7 Promise</h4>", "<h4>Always Open for Bookings</h4>"),
    ("Dr. Onyski is on call to respond to her patients' needs as soon as possible. As a patient of Wayside, you're never alone.",
     "Goldie's stylists are committed to giving every client a seamless experience — from the first DM at 11pm to the final blowout. The booking line never sleeps."),
    ("4907 International Pkwy, Suite 1041<br>Sanford, FL 32771",
     "1010 W Lake Mary Blvd<br>Lake Mary, FL 32746"),
    ("<div>(407) 732-4570</div>", "<div>(321) 363-1233</div>"),
    ("Mon–Thu 8a–5p · Fri 8a–1p", "Tue–Sat · By Appointment"),
    ("<strong>Wayside Concierge</strong> · Available 24/7",
     "<strong>Goldie Concierge</strong> · Available 24/7"),
    ("A patient of Wayside? Dr. Onyski will be notified immediately for urgent matters.",
     "A regular at Goldie? Your stylist will be notified directly for time-sensitive bookings."),
    # Bot greeting
    ("Good evening — you've reached the after-hours line for Wayside Family Dental. Dr. Onyski is unavailable right now, but I can help with most things and reach her directly if it's urgent.",
     "Welcome to Goldie. Your stylist's chair is empty for the night, but I'm the after-hours booking concierge — I can quote services, hold appointments, and answer most questions before you go to sleep."),
    # Chips
    ("{ label: '🦷 Tooth pain or emergency', value: 'emergency' },\n        { label: '✨ Implants or Invisalign', value: 'high-value' },\n        { label: '📅 New patient, want to book', value: 'new-patient' },\n        { label: '❓ A quick question', value: 'question' }",
     "{ label: '💇 Cut or style', value: 'emergency' },\n        { label: '🎨 Color, balayage, or highlights', value: 'high-value' },\n        { label: '✨ Extensions or treatments', value: 'new-patient' },\n        { label: '❓ A pricing question', value: 'question' }"),
    # Label map
    ("'emergency': 'I have tooth pain or an emergency',\n      'high-value': \"I'm interested in implants or Invisalign\",\n      'new-patient': \"I'm a new patient and want to book\",\n      'question': 'I just have a quick question',\n      'yes-existing': \"Yes, I'm an existing patient\",\n      'no-new': \"No, I'd be a new patient\",\n      'severe': 'Severe — keeping me up',\n      'moderate': \"Moderate — uncomfortable but manageable\",\n      'mild': 'Mild — just want to check it',\n      'implants': 'Dental implants',\n      'invisalign': 'Invisalign / clear aligners',\n      'both': 'Both, actually'",
     "'emergency': 'I want a cut or style',\n      'high-value': \"I want color, balayage, or highlights\",\n      'new-patient': \"I want extensions or a treatment\",\n      'question': 'I have a pricing question',\n      'yes-existing': \"Yes, I'm a regular\",\n      'no-new': \"No, I'd be new to Goldie\",\n      'severe': 'This week — special event',\n      'moderate': \"Within 2 weeks\",\n      'mild': 'Whenever there\\'s availability',\n      'implants': 'Hand-tied / luxury extensions',\n      'invisalign': 'Tape-in or clip-in extensions',\n      'both': 'Tell me what works'"),
    # Emergency path → cut/style booking
    ("// EMERGENCY PATH ----------------------------------\n    if (value === 'emergency') {\n      memory.concern = 'emergency';\n      // Step 1: Acknowledge | Step 2: Validate specifically\n      await addBotMessage(\n        `I'm sorry you're dealing with this — dental pain at this hour is genuinely awful, and you did the right thing reaching out. Let me get you to Dr. Onyski as quickly as possible.`,\n        900\n      );\n      // Step 3: Surface concern (calibrate urgency)\n      await addBotMessage(\n        `One quick question so I know how fast to escalate — how would you describe the pain right now?`,\n        1100,\n        [\n          { label: '🔴 Severe — keeping me up', value: 'severe' },\n          { label: '🟡 Moderate — uncomfortable', value: 'moderate' },\n          { label: '🟢 Mild — just want to check', value: 'mild' }\n        ]\n      );\n      return;\n    }",
     "// CUT/STYLE PATH ----------------------------------\n    if (value === 'emergency') {\n      memory.concern = 'cut-style';\n      await addBotMessage(\n        `Love that. Cut and style is the best place to start — most of Goldie's clients first came in for a simple cut and stayed for everything else.`,\n        900\n      );\n      await addBotMessage(\n        `Quick question so I know how to prioritize — when do you need it by?`,\n        1100,\n        [\n          { label: '🔴 This week — special event', value: 'severe' },\n          { label: '🟡 Within 2 weeks', value: 'moderate' },\n          { label: '🟢 Whenever there\\'s availability', value: 'mild' }\n        ]\n      );\n      return;\n    }"),
    # Severe urgency
    ("Understood. I'm flagging this as urgent and texting Dr. Onyski now — she'll call you back within 15 minutes.<br><br>While we wait, can I get your first name and best callback number? If swelling spreads to your eye, jaw, or neck, please go to the ER immediately — that's the one thing that can't wait.",
     "Got it — special event urgency. The team usually has a couple priority slots reserved each week for events. Let me get you on the calendar.<br><br>Can I get your first name and best phone number? Whatever the event is, we'll make sure you walk in feeling like the moment matters."),
    # Moderate
    ("Got it. Dr. Onyski will want to see you first thing — she keeps emergency slots open every morning at 8 AM specifically for situations like this.<br><br>What's your first name? I'll have her office pre-confirm with you by 7:30 AM.",
     "Perfect timeline. Goldie's stylists keep mid-week slots open for new clients — Tuesday or Thursday work best.<br><br>What's your first name? I'll have someone pre-confirm with you by tomorrow morning."),
    # High-value (color)
    ("// HIGH-VALUE PATH (implants/invisalign) ----------\n    if (value === 'high-value') {\n      memory.concern = 'high-value';\n      // Step 1+2: Acknowledge & validate\n      await addBotMessage(\n        `Great choice to reach out — both implants and Invisalign are major decisions and Dr. Onyski has been doing both since 2010, so you're in capable hands.<br><br>Which one were you curious about?`,\n        900,\n        [\n          { label: '🦷 Dental implants', value: 'implants' },\n          { label: '💎 Invisalign', value: 'invisalign' },\n          { label: '🔄 Both, actually', value: 'both' }\n        ]\n      );\n      return;\n    }",
     "// COLOR PATH ----------\n    if (value === 'high-value') {\n      memory.concern = 'color';\n      await addBotMessage(\n        `Smart move to reach out before you book — Goldie's colorists specialize in luxury color and would much rather hear what you're going for before you arrive than try to fix something rushed.<br><br>What kind of color are you thinking?`,\n        900,\n        [\n          { label: '🌟 Balayage', value: 'implants' },\n          { label: '✨ Full highlights', value: 'invisalign' },\n          { label: '🎨 Color correction', value: 'both' }\n        ]\n      );\n      return;\n    }"),
    # Color services elaboration
    ("if (value === 'implants' || value === 'invisalign' || value === 'both') {\n      memory.treatmentInterest = value;\n      const txt = value === 'implants' ? 'implants' : value === 'invisalign' ? 'Invisalign' : 'implants and Invisalign';",
     "if (value === 'implants' || value === 'invisalign' || value === 'both') {\n      memory.treatmentInterest = value;\n      const txt = value === 'implants' ? 'balayage' : value === 'invisalign' ? 'highlights' : 'a color correction';"),
    ("Most patients asking about ${txt} have one of two questions on their mind: <em>\"Am I a candidate?\"</em> and <em>\"What will it actually cost?\"</em><br><br>Both are best answered with a 30-minute consult — Dr. Onyski does a digital scan, reviews your options, and gives you a treatment plan with real numbers before you commit to anything. Wayside also accepts CareCredit if financing helps.<br><br>Want me to hold a consult slot for you this week?",
     "Most clients asking about ${txt} have one of two questions: <em>\"Will it look natural on me?\"</em> and <em>\"What will it actually cost?\"</em><br><br>Both are best answered in a 15-minute consultation — your colorist looks at your hair, walks through what's realistic, and gives you a real quote before you commit to anything. Color appointments at Goldie are typically 3-4 hours and run $250-$450 depending on length and complexity.<br><br>Want me to hold a consult slot this week?"),
    # Booking path
    ("`Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Dr. Onyski's schedule?`",
     "`Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on the schedule?`"),
    # New patient → extensions
    ("// NEW PATIENT PATH ---------------------------\n    if (value === 'new-patient') {\n      memory.concern = 'new-patient';\n      await addBotMessage(\n        `Welcome — Dr. Onyski has been welcoming new patients to Wayside since 2012, and most of our patients come from referrals, so it's nice when someone finds us directly.<br><br>What's your first name?`,\n        900\n      );\n      memory.collecting = 'name-new-patient';\n      return;\n    }",
     "// EXTENSIONS PATH ---------------------------\n    if (value === 'new-patient') {\n      memory.concern = 'extensions';\n      await addBotMessage(\n        `Extensions are one of Goldie's specialties — the team is certified in hand-tied, tape-in, and luxury fusion methods. Most clients are deciding between three things: length, fullness, and how much maintenance they want to commit to.<br><br>The best way to figure out the right method is a 30-minute consultation where the team walks you through samples and color-matches in person. What's your first name?`,\n        1300\n      );\n      memory.collecting = 'name-new-patient';\n      return;\n    }"),
    # Question path
    ("// QUESTION PATH -------------------------------\n    if (value === 'question') {\n      memory.concern = 'question';\n      await addBotMessage(\n        `Of course — go ahead and type your question and I'll do my best. If it's something Dr. Onyski needs to weigh in on personally, I'll route it to her and she'll get back to you in the morning.`,\n        900\n      );",
     "// QUESTION PATH -------------------------------\n    if (value === 'question') {\n      memory.concern = 'question';\n      await addBotMessage(\n        `Of course — type your question. If it's about pricing, services, or stylists, I can usually answer right now. If it's something specific to your hair history, the team will follow up tomorrow.`,\n        900\n      );"),
    # Name collection responses
    ("'name': `Thank you, ${memory.name}. What's the best phone number to reach you at? I want to make sure Dr. Onyski has it before tomorrow morning.`,",
     "'name': `Thank you, ${memory.name}. What's the best phone number to reach you at? The team will text you a confirmation in the morning.`,"),
    ("'name-new-patient': `Nice to meet you, ${memory.name}. What brings you in — a routine cleaning, a specific concern, or are you switching from another dentist?`,",
     "'name-new-patient': `Nice to meet you, ${memory.name}. What's bringing you to Goldie — switching from another stylist, a special event, or just ready for a change?`,"),
    ("'name-for-booking': `Thanks, ${memory.name}. What's the best phone number? Dr. Onyski's office will text you a confirmation within an hour of opening.`,",
     "'name-for-booking': `Thanks, ${memory.name}. What's your best phone number? The team will text you a confirmation in the morning.`,"),
    ("'name-phone': `Thank you, ${memory.name}. What's the best callback number? Dr. Onyski will call you within 15 minutes.`",
     "'name-phone': `Thank you, ${memory.name}. What's your best callback number? Someone from the team will reach you tomorrow.`"),
    # Booking confirmations
    ("Got it, ${memory.name} — I just paged Dr. Onyski. Expect a call from <strong>(407) 732-4570</strong> within 15 minutes.<br><br>Stay calm, sit upright if possible, and avoid hot or cold liquids until she calls. You're going to be okay.",
     "Got it, ${memory.name} — I'm flagging this for the team's morning attention. Expect a text from <strong>(321) 363-1233</strong> first thing tomorrow with a couple priority time slots.<br><br>If your event date is within the next 48 hours, please call us at opening — we'll make it work."),
    ("All set, ${memory.name}. Dr. Onyski's office will call (${text}) by 7:30 AM to confirm your appointment.<br><br>Anything else I can help with tonight?",
     "All set, ${memory.name}. The Goldie team will text you at ${text} tomorrow morning to confirm your appointment.<br><br>Anything else I can help with tonight?"),
    # Booking card
    ('<div class="booking-icon">W</div>', '<div class="booking-icon">G</div>'),
    ('<span class="value">Dr. Lyudmila A. Onyski</span>',
     '<span class="value">Goldie Stylist</span>'),
    ('<span class="value">4907 International Pkwy, Suite 1041</span>',
     '<span class="value">1010 W Lake Mary Blvd</span>'),
    # Booking treatment map
    ("'implants': 'Dental Implant Consultation',\n          'invisalign': 'Invisalign Consultation',\n          'both': 'Implant & Invisalign Consultation',\n          'emergency': 'Emergency Visit'",
     "'implants': 'Balayage Consultation',\n          'invisalign': 'Color / Highlights Consultation',\n          'both': 'Color Correction Consultation',\n          'emergency': 'Cut & Style Appointment'"),
    ("Perfect. Here's the hold I'm creating for Dr. Onyski:",
     "Perfect. Here's the hold I'm creating with the Goldie team:"),
    # Confirm message
    ("You're all set, ${memory.name}. Dr. Onyski has been notified, and you'll get a confirmation text from <strong>(407) 732-4570</strong> within the hour.<br><br>Have a good night — and thank you for choosing Wayside.",
     "You're all set, ${memory.name}. The Goldie team has been notified — you'll get a confirmation text from <strong>(321) 363-1233</strong> in the morning.<br><br>Take care tonight — see you soon."),
    ("No problem. Dr. Onyski has openings tomorrow at 8 AM, 11:30 AM, or 4:15 PM — which works best?",
     "No problem. Goldie has openings Tuesday at 11 AM, Wednesday at 3 PM, or Friday at 10 AM — which works best?"),
    # New patient reason
    ("Got it. Dr. Onyski opens new-patient slots Tuesday through Thursday — would tomorrow at 10:30 AM or Wednesday at 2 PM work better for you?",
     "Got it. Goldie's stylists keep new-client slots open Tuesday through Thursday — would Wednesday at 11 AM or Thursday at 2 PM work better?"),
    # Free question fallback
    ("Thanks for sending that over. I've logged your question for Dr. Onyski to review first thing in the morning — she or someone from her team will reach out by 10 AM.<br><br>Want me to also hold a consult slot in case you'd like to discuss it in person?",
     "Thanks for sending that over. I've logged your question for the Goldie team to review first thing in the morning — someone will reach out by 10 AM.<br><br>Want me to also hold a consult slot in case it's easier to discuss in person?"),
    # Default fallback chips
    ("`Thanks for sharing that. So I can route this correctly — would you say this is more of an emergency, a new patient request, or a question about a specific treatment?`",
     "`Thanks for sharing that. So I can route this correctly — are you most interested in a cut/style, a color service, extensions, or pricing info?`"),
    ("[\n        { label: '🦷 Emergency', value: 'emergency' },\n        { label: '📅 New patient', value: 'new-patient' },\n        { label: '✨ Treatment question', value: 'high-value' }\n      ]",
     "[\n        { label: '💇 Cut / Style', value: 'emergency' },\n        { label: '🎨 Color', value: 'high-value' },\n        { label: '✨ Extensions', value: 'new-patient' }\n      ]"),
    # Cleanup - phone replacements
    ("(407) 732-4570", "(321) 363-1233"),
]

GOLDIE_CLEANUP = [
    ("Wayside Family Dental", "Goldie Salon"),
    ("Wayside", "Goldie"),
    ("Dr. Lyudmila A. Onyski", "the Goldie team"),
    ("Dr. Onyski", "the team"),
    ("Onyski", "Goldie"),
]

# ----------------------------------------------------------------------------
# PIG FLOYD'S URBAN BARBAKOA — BBQ & tacos, Mills 50, Thomas (owner)
# Base: wayside.html (dental → restaurant adaptation)
# ----------------------------------------------------------------------------
PIGFLOYDS_SUBS = [
    ("Wayside Family Dental — After-Hours Concierge | Powered by Velo AI",
     "Pig Floyd's Urban Barbakoa — Reservations & Catering Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Wayside Family Dental.",
     "This is a live demo built by Velo AI for Pig Floyd's Urban Barbakoa."),
    ("Sanford, Florida · Est. 2012", "Mills 50, Orlando · Slow-Smoked"),
    ('<h1 class="practice-name">Wayside Family Dental</h1>',
     "<h1 class=\"practice-name\">Pig Floyd's Urban Barbakoa</h1>"),
    ('<p class="practice-doctor">Dr. Lyudmila A. Onyski, DDS</p>',
     '<p class="practice-doctor">Thomas, Owner</p>'),
    ("<h4>The 24/7 Promise</h4>", "<h4>Always Open for Bookings</h4>"),
    ("Dr. Onyski is on call to respond to her patients' needs as soon as possible. As a patient of Wayside, you're never alone.",
     "Pig Floyd's runs hot during dinner service and the team can't always pause to answer calls — but reservations, takeout, and catering inquiries get captured around the clock."),
    ("4907 International Pkwy, Suite 1041<br>Sanford, FL 32771",
     "1326 N Mills Ave<br>Orlando, FL 32803"),
    ("<div>(407) 732-4570</div>", "<div>(407) 203-0866</div>"),
    ("Mon–Thu 8a–5p · Fri 8a–1p", "Tue–Sun · Lunch & Dinner Service"),
    ("<strong>Wayside Concierge</strong> · Available 24/7",
     "<strong>Pig Floyd's Concierge</strong> · Available 24/7"),
    ("A patient of Wayside? Dr. Onyski will be notified immediately for urgent matters.",
     "Catering or large party? Thomas will be notified directly for time-sensitive bookings."),
    # Greeting
    ("Good evening — you've reached the after-hours line for Wayside Family Dental. Dr. Onyski is unavailable right now, but I can help with most things and reach her directly if it's urgent.",
     "Welcome to Pig Floyd's. The dining room is loud and the smokers are working — the team can't always pick up. I'm the after-hours line: I can take reservations, quote catering, and answer most menu questions before service tomorrow."),
    # Chips
    ("{ label: '🦷 Tooth pain or emergency', value: 'emergency' },\n        { label: '✨ Implants or Invisalign', value: 'high-value' },\n        { label: '📅 New patient, want to book', value: 'new-patient' },\n        { label: '❓ A quick question', value: 'question' }",
     "{ label: '🍽️ Reservation', value: 'emergency' },\n        { label: '🎉 Catering or large party', value: 'high-value' },\n        { label: '🛍️ Pickup or takeout', value: 'new-patient' },\n        { label: '❓ Menu / hours question', value: 'question' }"),
    ("'emergency': 'I have tooth pain or an emergency',\n      'high-value': \"I'm interested in implants or Invisalign\",\n      'new-patient': \"I'm a new patient and want to book\",\n      'question': 'I just have a quick question',\n      'yes-existing': \"Yes, I'm an existing patient\",\n      'no-new': \"No, I'd be a new patient\",\n      'severe': 'Severe — keeping me up',\n      'moderate': \"Moderate — uncomfortable but manageable\",\n      'mild': 'Mild — just want to check it',\n      'implants': 'Dental implants',\n      'invisalign': 'Invisalign / clear aligners',\n      'both': 'Both, actually'",
     "'emergency': 'I want to make a reservation',\n      'high-value': \"I'm interested in catering or a large party\",\n      'new-patient': \"I want pickup or takeout\",\n      'question': 'I have a menu or hours question',\n      'yes-existing': \"Yes, I've eaten here before\",\n      'no-new': \"No, first time\",\n      'severe': 'Tonight or tomorrow',\n      'moderate': \"Within the week\",\n      'mild': 'Whatever works',\n      'implants': 'Corporate / office',\n      'invisalign': 'Wedding / event',\n      'both': 'Family / celebration'"),
    # Reservation path (was emergency)
    ("// EMERGENCY PATH ----------------------------------\n    if (value === 'emergency') {\n      memory.concern = 'emergency';\n      // Step 1: Acknowledge | Step 2: Validate specifically\n      await addBotMessage(\n        `I'm sorry you're dealing with this — dental pain at this hour is genuinely awful, and you did the right thing reaching out. Let me get you to Dr. Onyski as quickly as possible.`,\n        900\n      );\n      // Step 3: Surface concern (calibrate urgency)\n      await addBotMessage(\n        `One quick question so I know how fast to escalate — how would you describe the pain right now?`,\n        1100,\n        [\n          { label: '🔴 Severe — keeping me up', value: 'severe' },\n          { label: '🟡 Moderate — uncomfortable', value: 'moderate' },\n          { label: '🟢 Mild — just want to check', value: 'mild' }\n        ]\n      );\n      return;\n    }",
     "// RESERVATION PATH ----------------------------------\n    if (value === 'emergency') {\n      memory.concern = 'reservation';\n      await addBotMessage(\n        `Awesome — let's get you a table.`,\n        700\n      );\n      await addBotMessage(\n        `When are you thinking?`,\n        900,\n        [\n          { label: '🔴 Tonight or tomorrow', value: 'severe' },\n          { label: '🟡 Within the week', value: 'moderate' },\n          { label: '🟢 Whatever works', value: 'mild' }\n        ]\n      );\n      return;\n    }"),
    # Severe → tonight reservation
    ("Understood. I'm flagging this as urgent and texting Dr. Onyski now — she'll call you back within 15 minutes.<br><br>While we wait, can I get your first name and best callback number? If swelling spreads to your eye, jaw, or neck, please go to the ER immediately — that's the one thing that can't wait.",
     "Got it — same-night reservations get tight quickly during peak service. Let me check the books and get back to you. While I do that, can I get your first name, party size, and a phone number? If you're aiming for tonight in the next hour, please also call (407) 203-0866 directly — we hold a few walk-in seats."),
    ("Got it. Dr. Onyski will want to see you first thing — she keeps emergency slots open every morning at 8 AM specifically for situations like this.<br><br>What's your first name? I'll have her office pre-confirm with you by 7:30 AM.",
     "Got it. The team typically has good availability mid-week — Tuesday and Wednesday have the most flexibility for parties of 4 or more.<br><br>What's your first name and party size? I'll have someone pre-confirm with you in the morning."),
    # Catering path
    ("// HIGH-VALUE PATH (implants/invisalign) ----------\n    if (value === 'high-value') {\n      memory.concern = 'high-value';\n      // Step 1+2: Acknowledge & validate\n      await addBotMessage(\n        `Great choice to reach out — both implants and Invisalign are major decisions and Dr. Onyski has been doing both since 2010, so you're in capable hands.<br><br>Which one were you curious about?`,\n        900,\n        [\n          { label: '🦷 Dental implants', value: 'implants' },\n          { label: '💎 Invisalign', value: 'invisalign' },\n          { label: '🔄 Both, actually', value: 'both' }\n        ]\n      );\n      return;\n    }",
     "// CATERING PATH ----------\n    if (value === 'high-value') {\n      memory.concern = 'catering';\n      await addBotMessage(\n        `Catering is one of Pig Floyd's strengths — the smoker doesn't sleep, so we can scale up for almost any event. What kind of event?`,\n        900,\n        [\n          { label: '💼 Corporate / office', value: 'implants' },\n          { label: '💒 Wedding / event', value: 'invisalign' },\n          { label: '🎉 Family / celebration', value: 'both' }\n        ]\n      );\n      return;\n    }"),
    ("if (value === 'implants' || value === 'invisalign' || value === 'both') {\n      memory.treatmentInterest = value;\n      const txt = value === 'implants' ? 'implants' : value === 'invisalign' ? 'Invisalign' : 'implants and Invisalign';",
     "if (value === 'implants' || value === 'invisalign' || value === 'both') {\n      memory.treatmentInterest = value;\n      const txt = value === 'implants' ? 'corporate catering' : value === 'invisalign' ? 'wedding catering' : 'family-style catering';"),
    ("Most patients asking about ${txt} have one of two questions on their mind: <em>\"Am I a candidate?\"</em> and <em>\"What will it actually cost?\"</em><br><br>Both are best answered with a 30-minute consult — Dr. Onyski does a digital scan, reviews your options, and gives you a treatment plan with real numbers before you commit to anything. Wayside also accepts CareCredit if financing helps.<br><br>Want me to hold a consult slot for you this week?",
     "Most clients asking about ${txt} are wondering: <em>\"How many people can you feed?\"</em> and <em>\"What's it going to cost?\"</em><br><br>Pig Floyd's catering ranges from BBQ trays for 10 people up to full-service events for 200+. Pricing usually lands $18-32 per person depending on protein mix and service style. Thomas does a free 15-minute call to scope events before quoting — that way the quote is real, not generic.<br><br>Want me to hold a slot this week?"),
    # Booking
    ("`Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Dr. Onyski's schedule?`",
     "`Perfect. Let me hold ${timeMap[value]} for you. What's your first name and party size?`"),
    # New patient → pickup
    ("// NEW PATIENT PATH ---------------------------\n    if (value === 'new-patient') {\n      memory.concern = 'new-patient';\n      await addBotMessage(\n        `Welcome — Dr. Onyski has been welcoming new patients to Wayside since 2012, and most of our patients come from referrals, so it's nice when someone finds us directly.<br><br>What's your first name?`,\n        900\n      );\n      memory.collecting = 'name-new-patient';\n      return;\n    }",
     "// PICKUP/TAKEOUT PATH ---------------------------\n    if (value === 'new-patient') {\n      memory.concern = 'pickup';\n      await addBotMessage(\n        `Pickup orders go through our online system — fastest way is to order at pigfloyds.com/order or call (407) 203-0866 during service. If you want me to text you the link or hold a name in the system for tomorrow, what's your first name?`,\n        1200\n      );\n      memory.collecting = 'name-new-patient';\n      return;\n    }"),
    # Question
    ("// QUESTION PATH -------------------------------\n    if (value === 'question') {\n      memory.concern = 'question';\n      await addBotMessage(\n        `Of course — go ahead and type your question and I'll do my best. If it's something Dr. Onyski needs to weigh in on personally, I'll route it to her and she'll get back to you in the morning.`,\n        900\n      );",
     "// QUESTION PATH -------------------------------\n    if (value === 'question') {\n      memory.concern = 'question';\n      await addBotMessage(\n        `Of course — type your question. Hours, menu items, dietary stuff (we have vegan smoke options), or anything specific to a dish — I can usually answer right now.`,\n        900\n      );"),
    # Name responses
    ("'name': `Thank you, ${memory.name}. What's the best phone number to reach you at? I want to make sure Dr. Onyski has it before tomorrow morning.`,",
     "'name': `Thank you, ${memory.name}. What's the best phone number? The team will text you a confirmation in the morning.`,"),
    ("'name-new-patient': `Nice to meet you, ${memory.name}. What brings you in — a routine cleaning, a specific concern, or are you switching from another dentist?`,",
     "'name-new-patient': `Nice to meet you, ${memory.name}. What's the order — or do you want me to text you the menu link?`,"),
    ("'name-for-booking': `Thanks, ${memory.name}. What's the best phone number? Dr. Onyski's office will text you a confirmation within an hour of opening.`,",
     "'name-for-booking': `Thanks, ${memory.name}. Phone number? The team will text confirmation by 11 AM.`,"),
    ("'name-phone': `Thank you, ${memory.name}. What's the best callback number? Dr. Onyski will call you within 15 minutes.`",
     "'name-phone': `Thank you, ${memory.name}. Phone number? Someone will call you back as soon as the dining room slows.`"),
    ("Got it, ${memory.name} — I just paged Dr. Onyski. Expect a call from <strong>(407) 732-4570</strong> within 15 minutes.<br><br>Stay calm, sit upright if possible, and avoid hot or cold liquids until she calls. You're going to be okay.",
     "Got it, ${memory.name}. I'm flagging this for the team — expect a call from <strong>(407) 203-0866</strong> as soon as the dining room slows. If you absolutely need tonight in the next hour, please also call directly. We hold a few walk-in seats."),
    ("All set, ${memory.name}. Dr. Onyski's office will call (${text}) by 7:30 AM to confirm your appointment.<br><br>Anything else I can help with tonight?",
     "All set, ${memory.name}. We'll text ${text} in the morning to confirm. Anything else?"),
    # Booking card
    ('<div class="booking-icon">W</div>', '<div class="booking-icon">P</div>'),
    ('<span class="value">Dr. Lyudmila A. Onyski</span>',
     "<span class=\"value\">Pig Floyd's Team</span>"),
    ('<span class="value">4907 International Pkwy, Suite 1041</span>',
     '<span class="value">1326 N Mills Ave, Orlando</span>'),
    ("'implants': 'Dental Implant Consultation',\n          'invisalign': 'Invisalign Consultation',\n          'both': 'Implant & Invisalign Consultation',\n          'emergency': 'Emergency Visit'",
     "'implants': 'Corporate Catering Consult',\n          'invisalign': 'Event Catering Consult',\n          'both': 'Family Catering Consult',\n          'emergency': 'Reservation'"),
    ("Perfect. Here's the hold I'm creating for Dr. Onyski:",
     "Perfect. Here's the hold I'm creating for the Pig Floyd's team:"),
    ("You're all set, ${memory.name}. Dr. Onyski has been notified, and you'll get a confirmation text from <strong>(407) 732-4570</strong> within the hour.<br><br>Have a good night — and thank you for choosing Wayside.",
     "You're all set, ${memory.name}. The team has been notified — you'll get a confirmation text from <strong>(407) 203-0866</strong> by mid-morning.<br><br>Take care tonight — see you at the smoker."),
    ("No problem. Dr. Onyski has openings tomorrow at 8 AM, 11:30 AM, or 4:15 PM — which works best?",
     "No problem. Pig Floyd's has tables available Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM — which works best?"),
    ("Got it. Dr. Onyski opens new-patient slots Tuesday through Thursday — would tomorrow at 10:30 AM or Wednesday at 2 PM work better for you?",
     "Got it. Want me to text the menu link to your phone, or hold an order ready for pickup tomorrow?"),
    ("Thanks for sending that over. I've logged your question for Dr. Onyski to review first thing in the morning — she or someone from her team will reach out by 10 AM.<br><br>Want me to also hold a consult slot in case you'd like to discuss it in person?",
     "Thanks for sending that over. The team will get back to you by mid-morning. Want me to also hold a reservation slot in case you'd like to come in?"),
    ("`Thanks for sharing that. So I can route this correctly — would you say this is more of an emergency, a new patient request, or a question about a specific treatment?`",
     "`Thanks for sharing. So I can route this correctly — are you most interested in a reservation, catering / large party, pickup, or a menu question?`"),
    ("[\n        { label: '🦷 Emergency', value: 'emergency' },\n        { label: '📅 New patient', value: 'new-patient' },\n        { label: '✨ Treatment question', value: 'high-value' }\n      ]",
     "[\n        { label: '🍽️ Reservation', value: 'emergency' },\n        { label: '🎉 Catering', value: 'high-value' },\n        { label: '🛍️ Pickup', value: 'new-patient' }\n      ]"),
    ("(407) 732-4570", "(407) 203-0866"),
]

PIGFLOYDS_CLEANUP = [
    ("Wayside Family Dental", "Pig Floyd's"),
    ("Wayside", "Pig Floyd's"),
    ("Dr. Lyudmila A. Onyski", "Thomas"),
    ("Dr. Onyski", "the team"),
    ("Onyski", "Pig Floyd's"),
]

# ----------------------------------------------------------------------------
# BACÁN — Michelin Latin fine dining at Lake Nona Wave Hotel
# Base: pigfloyds.html (already restaurant-adapted)
# ----------------------------------------------------------------------------
BACAN_SUBS = [
    ("Pig Floyd's Urban Barbakoa — Reservations & Catering Concierge | Powered by Velo AI",
     "BACÁN — Reservations & Private Dining Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Pig Floyd's Urban Barbakoa.",
     "This is a live demo built by Velo AI for BACÁN at Lake Nona Wave Hotel."),
    ("Mills 50, Orlando · Slow-Smoked", "Lake Nona, FL · Michelin-Recognized"),
    ("<h1 class=\"practice-name\">Pig Floyd's Urban Barbakoa</h1>",
     '<h1 class="practice-name">BACÁN</h1>'),
    ('<p class="practice-doctor">Thomas, Owner</p>',
     '<p class="practice-doctor">Chef Guillaume Robin</p>'),
    ("Pig Floyd's runs hot during dinner service and the team can't always pause to answer calls — but reservations, takeout, and catering inquiries get captured around the clock.",
     "BACÁN runs a refined dinner service where the team can't always pause to answer the phone — but reservations, dietary inquiries, and private dining requests get captured around the clock."),
    ("1326 N Mills Ave<br>Orlando, FL 32803",
     "6500 Tavistock Lakes Blvd<br>Lake Nona, FL 32827"),
    ("(407) 203-0866", "(407) 675-2000"),
    ("Tue–Sun · Lunch & Dinner Service", "Tue–Sat · Dinner Service"),
    ("<strong>Pig Floyd's Concierge</strong> · Available 24/7",
     "<strong>BACÁN Concierge</strong> · Available 24/7"),
    ("Catering or large party? Thomas will be notified directly for time-sensitive bookings.",
     "Hotel guest or private dining inquiry? Chef Robin's team is notified directly."),
    ("Welcome to Pig Floyd's. The dining room is loud and the smokers are working — the team can't always pick up. I'm the after-hours line: I can take reservations, quote catering, and answer most menu questions before service tomorrow.",
     "Welcome to BACÁN. The dining room is mid-service and the team can't always pick up — but I'm here. I can take reservations, scope private dining, walk you through dietary considerations, and have anything time-sensitive in front of Chef Robin before service tomorrow."),
    # Catering chips → private dining
    ("{ label: '🍽️ Reservation', value: 'emergency' },\n        { label: '🎉 Catering or large party', value: 'high-value' },\n        { label: '🛍️ Pickup or takeout', value: 'new-patient' },\n        { label: '❓ Menu / hours question', value: 'question' }",
     "{ label: '🍽️ Reservation', value: 'emergency' },\n        { label: '🥂 Private dining or events', value: 'high-value' },\n        { label: '🥗 Menu / dietary question', value: 'new-patient' },\n        { label: '❓ Hotel guest concierge', value: 'question' }"),
    # Pickup → menu/dietary path adaptation
    ("// PICKUP/TAKEOUT PATH ---------------------------\n    if (value === 'new-patient') {\n      memory.concern = 'pickup';\n      await addBotMessage(\n        `Pickup orders go through our online system — fastest way is to order at pigfloyds.com/order or call (407) 203-0866 during service. If you want me to text you the link or hold a name in the system for tomorrow, what's your first name?`,\n        1200\n      );\n      memory.collecting = 'name-new-patient';\n      return;\n    }",
     "// MENU/DIETARY PATH ---------------------------\n    if (value === 'new-patient') {\n      memory.concern = 'menu';\n      await addBotMessage(\n        `Of course — Chef Robin's menu rotates seasonally and the team accommodates most dietary needs (vegan, gluten, allergens) when given a few hours notice. What's the question, or which dietary consideration are you working with? I'll either answer it now or get it to the team for your reservation.`,\n        1200\n      );\n      memory.collecting = 'free-question';\n      return;\n    }"),
    # Catering language → private dining
    ("Catering is one of Pig Floyd's strengths — the smoker doesn't sleep, so we can scale up for almost any event. What kind of event?",
     "Private dining at BACÁN can accommodate intimate dinners up to full restaurant buyouts for hotel events. What kind of event are you considering?"),
    ("Pig Floyd's catering ranges from BBQ trays for 10 people up to full-service events for 200+. Pricing usually lands $18-32 per person depending on protein mix and service style. Thomas does a free 15-minute call to scope events before quoting — that way the quote is real, not generic.",
     "Private dining at BACÁN starts at parties of 8 with a curated tasting menu, and scales to full restaurant buyouts. Pricing is typically $125-225 per person depending on the menu and beverage program. Chef Robin's team does a planning call before quoting — that way the menu fits the event, not the other way around."),
    ("'implants': 'corporate catering',\n      'invisalign': 'wedding catering',\n      'both': 'family-style catering'",
     "'implants': 'private dining',\n      'invisalign': 'wedding receptions',\n      'both': 'restaurant buyouts'"),
    ("'implants': 'Corporate Catering Consult',\n          'invisalign': 'Event Catering Consult',\n          'both': 'Family Catering Consult',\n          'emergency': 'Reservation'",
     "'implants': 'Private Dining Consult',\n          'invisalign': 'Wedding Reception Consult',\n          'both': 'Restaurant Buyout Consult',\n          'emergency': 'Reservation'"),
    # Question path → hotel guest concierge
    ("// QUESTION PATH -------------------------------\n    if (value === 'question') {\n      memory.concern = 'question';\n      await addBotMessage(\n        `Of course — type your question. Hours, menu items, dietary stuff (we have vegan smoke options), or anything specific to a dish — I can usually answer right now.`,\n        900\n      );",
     "// HOTEL GUEST PATH -------------------------------\n    if (value === 'question') {\n      memory.concern = 'hotel';\n      await addBotMessage(\n        `Welcome — are you a Lake Nona Wave Hotel guest looking to book at BACÁN? I can hold a table prioritized for hotel guests, walk through the menu, or answer hours and dress code questions. What can I help with?`,\n        1100\n      );"),
    ("(407) 203-0866", "(407) 675-2000"),
    # Pig Floyd's wholesale rename
    ("Pig Floyd's Urban Barbakoa", "BACÁN"),
    ("Pig Floyd's", "BACÁN"),
    ("Thomas", "Chef Robin"),
    ("the smoker doesn't sleep", "the kitchen never stops planning"),
    ("at the smoker", "at BACÁN"),
    ("after-hours and during dinner rush", "after dinner service"),
    ("see you at the smoker", "see you at BACÁN"),
    ('<div class="booking-icon">P</div>', '<div class="booking-icon">B</div>'),
    ("<span class=\"value\">Pig Floyd's Team</span>", '<span class="value">BACÁN Team</span>'),
    ('<span class="value">1326 N Mills Ave, Orlando</span>',
     '<span class="value">6500 Tavistock Lakes Blvd, Lake Nona</span>'),
]

BACAN_CLEANUP = [
    ("pigfloyds.com", "bacanlakenona.com"),
]

# ----------------------------------------------------------------------------
# KADENCE — Michelin omakase, Audubon Park
# Base: pigfloyds.html
# ----------------------------------------------------------------------------
KADENCE_SUBS = [
    ("Pig Floyd's Urban Barbakoa — Reservations & Catering Concierge | Powered by Velo AI",
     "Kadence — Omakase Reservations Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Pig Floyd's Urban Barbakoa.",
     "This is a live demo built by Velo AI for Kadence."),
    ("Mills 50, Orlando · Slow-Smoked", "Audubon Park, Orlando · 1 Michelin Star"),
    ("<h1 class=\"practice-name\">Pig Floyd's Urban Barbakoa</h1>",
     '<h1 class="practice-name">Kadence</h1>'),
    ('<p class="practice-doctor">Thomas, Owner</p>',
     '<p class="practice-doctor">The Kadence Team</p>'),
    ("Pig Floyd's runs hot during dinner service and the team can't always pause to answer calls — but reservations, takeout, and catering inquiries get captured around the clock.",
     "Kadence runs a 9-seat omakase counter where the chefs can't pause for the phone — but reservation requests, waitlist inquiries, and dietary considerations get captured around the clock."),
    ("1326 N Mills Ave<br>Orlando, FL 32803",
     "1809 Winter Park Rd<br>Orlando, FL 32803"),
    ("(407) 203-0866", "(407) 270-6997"),
    ("Tue–Sun · Lunch & Dinner Service", "Tue–Sat · Two Seatings Per Night"),
    ("<strong>Pig Floyd's Concierge</strong> · Available 24/7",
     "<strong>Kadence Concierge</strong> · Available 24/7"),
    ("Catering or large party? Thomas will be notified directly for time-sensitive bookings.",
     "Cancellation, dietary, or buyout request? The team is notified directly."),
    ("Welcome to Pig Floyd's. The dining room is loud and the smokers are working — the team can't always pick up. I'm the after-hours line: I can take reservations, quote catering, and answer most menu questions before service tomorrow.",
     "Welcome to Kadence. We're a 9-seat omakase counter, so service is intimate and the chefs can't pause to answer the phone. I'm here to take reservation requests, manage the waitlist, walk through dietary considerations, and route anything special to the team."),
    ("{ label: '🍽️ Reservation', value: 'emergency' },\n        { label: '🥂 Private dining or events', value: 'high-value' },\n        { label: '🥗 Menu / dietary question', value: 'new-patient' },\n        { label: '❓ Hotel guest concierge', value: 'question' }",
     "{ label: '🍣 Reservation request', value: 'emergency' },\n        { label: '🎌 Private buyout / event', value: 'high-value' },\n        { label: '🍵 Dietary considerations', value: 'new-patient' },\n        { label: '❓ Waitlist or last-minute', value: 'question' }"),
    ("Welcome — are you a Lake Nona Wave Hotel guest looking to book at BACÁN? I can hold a table prioritized for hotel guests, walk through the menu, or answer hours and dress code questions. What can I help with?",
     "Of course — Kadence often has last-minute openings due to cancellations. I can add you to tonight's or this week's waitlist with priority based on flexibility. Tell me your party size and which night(s) work, and I'll text you immediately if a seat opens up."),
    ("Private dining at BACÁN can accommodate intimate dinners up to full restaurant buyouts for hotel events. What kind of event are you considering?",
     "Buyouts at Kadence are unique — the entire 9-seat counter for one party, custom omakase progression. The chefs love planning these. What's the occasion?"),
    ("Private dining at BACÁN starts at parties of 8 with a curated tasting menu, and scales to full restaurant buyouts. Pricing is typically $125-225 per person depending on the menu and beverage program. Chef Robin's team does a planning call before quoting — that way the menu fits the event, not the other way around.",
     "Buyouts run $300-$500 per seat depending on the omakase progression and beverage pairing. The team does a planning call to understand occasion and dietary needs before quoting — that way the menu becomes part of the experience."),
    # Kadence specifically wants reservation flow not catering
    ("// MENU/DIETARY PATH",
     "// DIETARY PATH"),
    ("Of course — Chef Robin's menu rotates seasonally and the team accommodates most dietary needs (vegan, gluten, allergens) when given a few hours notice. What's the question, or which dietary consideration are you working with? I'll either answer it now or get it to the team for your reservation.",
     "Of course — Kadence is a 12-course omakase, so dietary accommodations need to be planned in advance. The team handles most allergens (shellfish, gluten, sesame) and can craft a fully vegan or pescatarian progression with 48hrs notice. What's the consideration?"),
    ('"implants": "private dining",\n      "invisalign": "wedding receptions",\n      "both": "restaurant buyouts"',
     '"implants": "buyout dinners",\n      "invisalign": "anniversary or proposal",\n      "both": "milestone celebration"'),
    ('"implants": "Private Dining Consult",\n          "invisalign": "Wedding Reception Consult",\n          "both": "Restaurant Buyout Consult",\n          "emergency": "Reservation"',
     '"implants": "Buyout Planning Consult",\n          "invisalign": "Special Occasion Reservation",\n          "both": "Milestone Reservation",\n          "emergency": "Reservation Request"'),
    ("(407) 203-0866", "(407) 270-6997"),
    ("Pig Floyd's Urban Barbakoa", "Kadence"),
    ("Pig Floyd's", "Kadence"),
    ("Thomas", "the chefs"),
    ("the smoker doesn't sleep", "the chefs are obsessive"),
    ("see you at the smoker", "see you at the counter"),
    ('<div class="booking-icon">P</div>', '<div class="booking-icon">K</div>'),
    ("<span class=\"value\">Pig Floyd's Team</span>", '<span class="value">Kadence Team</span>'),
    ('<span class="value">1326 N Mills Ave, Orlando</span>',
     '<span class="value">1809 Winter Park Rd, Orlando</span>'),
]

KADENCE_CLEANUP = [
    ("pigfloyds.com", "kadenceorlando.com"),
]

# ----------------------------------------------------------------------------
# MARCIA'S LOOKS — Hair color/extensions, Downtown Orlando
# Base: goldie.html (already salon-adapted)
# ----------------------------------------------------------------------------
MARCIAS_SUBS = [
    ("Goldie Salon — After-Hours Booking Concierge | Powered by Velo AI",
     "Marcia's Looks — Booking Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Goldie Salon.",
     "This is a live demo built by Velo AI for Marcia's Looks."),
    ("Lake Mary, Florida · Luxury Hair", "Downtown Orlando · Color & Extensions"),
    ('<h1 class="practice-name">Goldie Salon</h1>',
     "<h1 class=\"practice-name\">Marcia's Looks</h1>"),
    ('<p class="practice-doctor">The Goldie Team</p>',
     '<p class="practice-doctor">Marcia, Owner & Lead Stylist</p>'),
    ("Goldie's stylists are committed to giving every client a seamless experience — from the first DM at 11pm to the final blowout. The booking line never sleeps.",
     "Marcia's specializes in color and hand-tied extensions for clients who care about the details. The booking line is always open — DM at 11pm, walk in tomorrow."),
    ("1010 W Lake Mary Blvd<br>Lake Mary, FL 32746",
     "418 N Orange Ave<br>Orlando, FL 32801"),
    ("(321) 363-1233", "(321) 588-1975"),
    ("Tue–Sat · By Appointment", "Tue–Sat · By Appointment"),
    ("<strong>Goldie Concierge</strong> · Available 24/7",
     "<strong>Marcia's Concierge</strong> · Available 24/7"),
    ("A regular at Goldie? Your stylist will be notified directly for time-sensitive bookings.",
     "A regular at Marcia's? She'll be notified directly for time-sensitive bookings."),
    ("Welcome to Goldie. Your stylist's chair is empty for the night, but I'm the after-hours booking concierge — I can quote services, hold appointments, and answer most questions before you go to sleep.",
     "Welcome to Marcia's Looks. Marcia is wrapped for the day, but I'm her after-hours booking concierge — I can quote services, hold appointments, and answer color or extensions questions before tomorrow."),
    ("Goldie", "Marcia's"),
    ("the Goldie team", "Marcia"),
    ("Goldie's stylists", "Marcia"),
    ("Goldie's colorists", "Marcia"),
    ("Color appointments at Goldie", "Color appointments at Marcia's"),
    ("the Goldie team", "Marcia"),
    ("the team", "Marcia"),  # in dialogue contexts where Goldie was the team
    ("Goldie's specialties", "Marcia's specialties"),
    ('<div class="booking-icon">G</div>', '<div class="booking-icon">M</div>'),
    ('<span class="value">Goldie Stylist</span>',
     '<span class="value">Marcia</span>'),
    ('<span class="value">1010 W Lake Mary Blvd</span>',
     '<span class="value">418 N Orange Ave, Orlando</span>'),
    ("(321) 363-1233", "(321) 588-1975"),
]

MARCIAS_CLEANUP = [
    ("Goldie", "Marcia's"),
]

# ----------------------------------------------------------------------------
# VELIZ KATZ LAW — Family + estate planning, Maitland
# Base: ragland.html (already estate planning)
# ----------------------------------------------------------------------------
VELIZKATZ_SUBS = [
    ("Lance A. Ragland, P.A. — After-Hours Intake | Powered by Velo AI",
     "Veliz Katz Law — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Lance A. Ragland, P.A.",
     "This is a live demo built by Velo AI for Veliz Katz Law"),
    ("Winter Springs, Florida · Est. 2015", "Maitland, Florida · Family + Estate"),
    ('<h1 class="practice-name">Lance A. Ragland, P.A.</h1>',
     '<h1 class="practice-name">Veliz Katz Law</h1>'),
    ('<p class="practice-doctor">Lance A. Ragland, Esq.</p>',
     '<p class="practice-doctor">David Veliz &amp; Norberto Katz, Esq.</p>'),
    ("<h4>Available When You Need Him</h4>", "<h4>Two Practices, One Team</h4>"),
    ("Estate matters rarely surface during business hours. Lance is committed to being there for clients during life's most difficult transitions. You're never alone.",
     "Family law and estate planning both surface during life's hardest moments — divorce, custody, the death of a parent. David and Norberto are committed to being there during those transitions. You're never alone."),
    ("5750 Canton Cove<br>Winter Springs, FL 32708",
     "1936 Lee Rd<br>Maitland, FL 32751"),
    ("(407) 960-6069", "(407) 849-7072"),
    ("By Appointment · Mon–Fri 9a–5p", "Mon–Fri 9a–5p · Confidential consults"),
    ("<strong>Ragland Intake</strong> · Available 24/7",
     "<strong>Veliz Katz Intake</strong> · Available 24/7"),
    ("A current client of Lance's? He'll be notified directly for urgent matters.",
     "A current client? David or Norberto will be notified directly for urgent matters."),
    ("Good evening — you've reached the after-hours line for the Law Offices of Lance A. Ragland. Lance focuses entirely on estate planning, probate, and trust matters. He's unavailable right now, but I can take down what's on your mind and get him to reach back out.",
     "Good evening — you've reached the after-hours line for Veliz Katz Law. The firm handles family law and estate planning — divorce, custody, probate, and trust matters. Both attorneys are wrapped for the day, but everything you share with me is confidential. I'll take down what's on your mind and get the right attorney to reach back out."),
    # Different chip set — both family and estate
    ("{ label: '🕯️ I lost a loved one', value: 'probate' },\n        { label: '📜 Plan a will or trust', value: 'planning' },\n        { label: '🏥 Power of attorney / healthcare', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }",
     "{ label: '💔 Family law / divorce / custody', value: 'probate' },\n        { label: '🕯️ Estate / probate matter', value: 'planning' },\n        { label: '📜 Wills and trusts', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }"),
    ("'probate': \"I lost a loved one and need probate help\",\n      'planning': \"I'd like to plan a will or trust\",\n      'poa': \"I need a power of attorney or healthcare paperwork\"",
     "'probate': \"I have a family law matter\",\n      'planning': \"I lost a loved one or need probate help\",\n      'poa': \"I want to plan a will or trust\""),
    ("if (value === 'probate') {\n      memory.matter = 'probate';\n      await addBotMessage(\n        `I'm so sorry for your loss. Please take whatever time you need.<br><br>Lance has guided families through probate for nearly thirty years, and most of what feels overwhelming right now has a clear path forward. The two things that help him move quickly when he calls you back: who passed, and whether they had a will.`,",
     "if (value === 'probate') {\n      memory.matter = 'family';\n      await addBotMessage(\n        `Family law matters are some of the most personal calls a firm receives. David handles family law specifically, and the firm has helped clients through divorce, custody disputes, and modifications for over twenty years. The two things that help David move quickly: what's the situation, and whether kids are involved.`,"),
    ("`If you're able to share — who is this for?`,\n        900,\n        [\n          { label: 'Spouse', value: 'spouse' },\n          { label: 'Parent', value: 'parent' },\n          { label: 'Other family member', value: 'other-family' }\n        ]",
     "`If you're able to share — what's the situation?`,\n        900,\n        [\n          { label: 'Considering divorce', value: 'spouse' },\n          { label: 'Custody dispute', value: 'parent' },\n          { label: 'Modification or post-decree', value: 'other-family' }\n        ]"),
    ("'spouse': \"My spouse\",\n      'parent': \"A parent\",\n      'other-family': \"Another family member\"",
     "'spouse': \"Considering divorce\",\n      'parent': \"Custody dispute\",\n      'other-family': \"Modification matter\""),
    ("if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.relation = value;\n      await addBotMessage(\n        `Thank you. Did they have a will or any estate documents in place?`,\n        900,\n        [\n          { label: 'Yes, they had a will', value: 'has-will' },\n          { label: 'No', value: 'no-will' },\n          { label: \"I'm not sure\", value: 'unsure-will' }\n        ]\n      );\n      return;\n    }",
     "if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.situation = value;\n      await addBotMessage(\n        `Thank you. Are children involved?`,\n        900,\n        [\n          { label: 'Yes, with custody concerns', value: 'has-will' },\n          { label: 'Yes, but no current dispute', value: 'no-will' },\n          { label: 'No children', value: 'unsure-will' }\n        ]\n      );\n      return;\n    }"),
    ("memory.hasWill = value;\n      await addBotMessage(\n        `Got it. One more question, then I'll get this in front of Lance — is anything time-pressured? Sometimes accounts get frozen, or a property has a deadline. Other times there's just no rush.`,",
     "memory.children = value;\n      await addBotMessage(\n        `Got it. One more question — is there an active situation tonight (someone's safety, a court order being violated), or is this in a planning stage?`,"),
    ("'urgent-frozen': \"Yes — accounts are frozen / property at risk\",\n      'urgent-soon': \"Soon, but not in crisis\",\n      'urgent-planning': \"No urgency — just planning ahead\"",
     "'urgent-frozen': \"Active situation tonight\",\n      'urgent-soon': \"Important but not crisis\",\n      'urgent-planning': \"Just exploring my options\""),
    ("[\n          { label: '🔴 Yes — accounts frozen / property at risk', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not in crisis', value: 'urgent-soon' },\n          { label: '🟢 No urgency — just planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Active situation tonight', value: 'urgent-frozen' },\n          { label: '🟡 Important but not crisis', value: 'urgent-soon' },\n          { label: '🟢 Exploring my options', value: 'urgent-planning' }\n        ]"),
    # Severe response (modify Lance refs first)
    ("`Understood — that's exactly the kind of thing Lance wants to know about right away. I'm flagging this as priority and Lance will call you first thing tomorrow morning, before his appointments start.<br><br>Can I get your first name and best callback number? If a deadline is in the next 48 hours, please mention it.`",
     "`Understood — David wants to hear about active family law situations tonight if someone's safety is at stake. If anyone is in immediate danger, please call 911 first. Otherwise, I'm flagging this as priority and David will call you first thing tomorrow before his court calendar starts.<br><br>Can I get your first name and best callback number?`"),
    ("`Thank you — that helps. Lance opens his calendar Tuesday through Thursday for new probate matters and sets aside ninety minutes per consultation so nothing feels rushed.<br><br>What's your first name? I'll have him reach out by mid-morning to set a time that works.`",
     "`Thank you — that helps. David keeps confidential consultation slots Tuesday through Thursday for new family matters. The firm has been practicing family law and estate planning in Maitland for over twenty years.<br><br>What's your first name? I'll have him reach out tomorrow morning.`"),
    # Planning path → estate (instead of will/trust planning)
    ("if (value === 'planning') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart of you to think about this — most people put off estate planning for years and regret the procrastination. Lance has been doing wills, trusts, and estate plans exclusively since 2015, so this is exactly his bread and butter.<br><br>Most clients in your shoes are weighing one of two things: <em>\"Do I just need a will, or do I need a trust?\"</em> and <em>\"What's this going to cost me?\"</em><br><br>Both are answered properly in a one-hour consult — Lance reviews your situation, walks you through the difference, and gives you a flat-fee quote before you commit to anything. Want me to hold a slot this week or next?`,",
     "if (value === 'planning') {\n      memory.matter = 'estate';\n      await addBotMessage(\n        `I'm sorry — these calls are usually placed at one of the hardest moments. Norberto handles estate matters at the firm, including probate, trust administration, and the post-loss paperwork most families don't know how to navigate. The two things that help him move quickly: who passed, and whether they had any documents in place.<br><br>Want me to set up a confidential consultation this week or next?`,"),
    # POA path → wills and trusts
    ("if (value === 'poa') {\n      memory.matter = 'poa';\n      await addBotMessage(\n        `These conversations are hard — usually they come up because someone in the family is going through a health change. Lance can put together a power of attorney and healthcare surrogate quickly, often within a few days if needed.<br><br>Just so I get the right urgency to him: is this for an immediate situation, or planning ahead?`,",
     "if (value === 'poa') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart to think about this before you need it — most people put off estate planning until a crisis forces the conversation, which is exactly the wrong time. Norberto can put together wills, trusts, powers of attorney, and healthcare surrogates as a coordinated package.<br><br>Just so I route the right urgency: is this for planning ahead, or is something immediate driving the timing?`,"),
    ("[\n          { label: '🔴 Immediate — health is declining', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not crisis', value: 'urgent-soon' },\n          { label: '🟢 Planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Health change in family', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but no crisis', value: 'urgent-soon' },\n          { label: '🟢 Just planning ahead', value: 'urgent-planning' }\n        ]"),
    ("`Of course — go ahead and type your question. If it's something Lance needs to weigh in on personally, I'll route it to him and he'll get back to you in the morning. If it's something I can answer from his practice info, I'll do my best.`",
     "`Of course — type your question. The firm handles family law (David) and estate planning (Norberto), so I'll route it to whoever it fits best.`"),
    ('<div class="booking-icon">L</div>', '<div class="booking-icon">V</div>'),
    ('<span class="value">Lance A. Ragland, Esq.</span>',
     '<span class="value">David Veliz or Norberto Katz, Esq.</span>'),
    ('<span class="value">5750 Canton Cove, Winter Springs</span>',
     '<span class="value">1936 Lee Rd, Maitland</span>'),
    ("'planning': 'Estate Planning Consultation',\n          'poa': 'Power of Attorney Consultation',\n          'probate': 'Probate Consultation',\n          'question': 'General Consultation'",
     "'estate': 'Estate / Probate Consultation',\n          'planning': 'Estate Planning Consultation',\n          'family': 'Family Law Consultation',\n          'question': 'General Consultation'"),
    ("(407) 960-6069", "(407) 849-7072"),
    ("Lance has been notified", "The Veliz Katz team has been notified"),
    ("Lance will reach out", "The Veliz Katz attorneys will reach out"),
    ("Lance opens new-patient slots", "David opens consultation slots"),
    ("`No problem. Lance has openings", "`No problem. The firm has openings"),
    ("Lance ", "the team "),
    ("Lance's", "the firm's"),
    ("Lance.", "the firm."),
    ("Lance,", "the firm,"),
    ("his office (Debbie)", "the firm's paralegal"),
]

VELIZKATZ_CLEANUP = [
    ("Lance", "the team"),
    ("Ragland", "Veliz Katz"),
]

# ----------------------------------------------------------------------------
# CULLEN & HEMPHILL — PI / workers' comp, Winter Park
# Base: klausmanlaw.html (already PI-adapted)
# ----------------------------------------------------------------------------
CULLEN_SUBS = [
    ("Klausman Law — After-Hours Intake | Powered by Velo AI",
     "Cullen & Hemphill — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Klausman Law",
     "This is a live demo built by Velo AI for Cullen & Hemphill"),
    ("Winter Park, Florida · Est. 1998", "Winter Park, Florida · Personal Injury"),
    ('<h1 class="practice-name">Klausman Law</h1>',
     '<h1 class="practice-name">Cullen &amp; Hemphill</h1>'),
    ('<p class="practice-doctor">Glenn Klausman, Esq.</p>',
     '<p class="practice-doctor">Kim Cullen, Esq.</p>'),
    ("Accidents and insurance disputes don't wait for business hours. Glenn is committed to being the first call you can actually reach — and the last call you'll need to make.",
     "Accidents and workplace injuries don't wait for business hours. Kim is committed to being the first call you can actually reach — and the last call you'll need to make."),
    ("1101 N Lakemont Ave, Suite 200<br>Winter Park, FL 32792",
     "655 W Morse Blvd, Suite 100<br>Winter Park, FL 32789"),
    ("(407) 917-1718", "(407) 565-7386"),
    ("<strong>Klausman Intake</strong> · Available 24/7",
     "<strong>Cullen &amp; Hemphill Intake</strong> · Available 24/7"),
    ("Already a client? Glenn will be notified directly for urgent matters on your case.",
     "Already a client? Kim will be notified directly for urgent matters on your case."),
    # Bot greeting
    ("Good evening — you've reached the after-hours line for Klausman Law. Glenn handles personal injury and insurance disputes — accident cases, denied claims, and workers' comp. He's not available right this minute, but I can take down what happened and get him on a call with you fast.",
     "Good evening — you've reached the after-hours line for Cullen & Hemphill. Kim handles personal injury and workers' compensation cases — car accidents, slip-and-fall, workplace injuries, and denied claims. She's wrapped for the day, but I can take down what happened and get her on a call with you fast."),
    # Pronouns: he → she throughout
    ("Glenn has handled thousands of injury cases in 27 years",
     "Kim has handled hundreds of injury cases over her career"),
    ("the first thing he usually does",
     "the first thing she usually does"),
    ("when he calls back",
     "when she calls back"),
    ("Glenn wants to hear from you ASAP if you're hurt. I'm flagging this as priority and he'll call you within the hour during business hours, or first thing in the morning if it's late tonight.",
     "Kim wants to hear from you ASAP if you're hurt. I'm flagging this as priority and she'll call you within the hour during business hours, or first thing in the morning if it's late tonight."),
    ("Glenn offers free consultations for injury cases — no fee unless he wins your case. He'll review the situation, walk you through what your case might be worth, and explain the timeline so you know what to expect.",
     "Kim offers free consultations for injury cases — no fee unless she wins your case. She'll review the situation, walk you through what your case might be worth, and explain the timeline so you know what to expect."),
    ("Insurance denials are exactly what Glenn handles every week. Insurance companies count on people accepting the first 'no' — they're often wrong, and a properly contested claim can flip outcome and dollar amount dramatically.",
     "Insurance denials are exactly what Kim handles regularly. Insurance companies count on people accepting the first 'no' — they're often wrong, and a properly contested claim can flip outcome and dollar amount dramatically."),
    ("Both are answered in a free consultation — Glenn reviews your denial letter and policy, tells you straight whether you have a case, and only takes it if he thinks you'll win.",
     "Both are answered in a free consultation — Kim reviews your denial letter and policy, tells you straight whether you have a case, and only takes it if she thinks you'll win."),
    ("Workers' comp can feel impossible to navigate — most claimants are dealing with HR pressure, doctors who work for the employer, and a system designed to deny first and pay last. Glenn has handled hundreds of these cases.",
     "Workers' comp can feel impossible to navigate — most claimants are dealing with HR pressure, doctors who work for the employer, and a system designed to deny first and pay last. Kim has handled hundreds of these cases."),
    ("Of course — type your question. If it's something Glenn needs to weigh in on personally (case strategy, settlement evaluation, opposing counsel), I'll route it to him and he'll get back to you in the morning.",
     "Of course — type your question. If it's something Kim needs to weigh in on personally (case strategy, settlement evaluation, opposing counsel), I'll route it to her and she'll get back to you in the morning."),
    ('<div class="booking-icon">K</div>', '<div class="booking-icon">C</div>'),
    ('<span class="value">Glenn Klausman, Esq.</span>',
     '<span class="value">Kim Cullen, Esq.</span>'),
    ('<span class="value">1101 N Lakemont Ave, Winter Park</span>',
     '<span class="value">655 W Morse Blvd, Winter Park</span>'),
    ("(407) 917-1718", "(407) 565-7386"),
    ("Glenn has been notified", "Kim has been notified"),
    ("Glenn will reach out", "Kim will reach out"),
    ("Glenn opens his calendar", "Kim opens her calendar"),
    ("`No problem. Glenn has openings", "`No problem. Kim has openings"),
    # Final pronoun cleanup
    ("Glenn ", "Kim "),
    ("Glenn's", "Kim's"),
    ("Glenn.", "Kim."),
    ("Glenn,", "Kim,"),
    (" he calls", " she calls"),
    (" he wants to know", " she wants to know"),
    (" he wants to hear", " she wants to hear"),
    (" he'll call you", " she'll call you"),
    (" he handles", " she handles"),
    (" he reviews", " she reviews"),
    (" he thinks", " she thinks"),
    (" he gets back", " she gets back"),
    ("welcome from Glenn", "welcome from Kim"),
]

CULLEN_CLEANUP = [
    ("Glenn", "Kim"),
    ("Klausman Law", "Cullen & Hemphill"),
    ("Klausman", "Cullen & Hemphill"),
]

# ----------------------------------------------------------------------------
# PALMANO GROUP — Luxury RE, Winter Park
# Base: sunbright.html (already RE-adapted)
# ----------------------------------------------------------------------------
PALMANO_SUBS = [
    ("Sunbright Realty — After-Hours Lead Qualifier | Powered by Velo AI",
     "Palmano Group — Luxury RE Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Sunbright Realty.",
     "This is a live demo built by Velo AI for Palmano Group."),
    ("Clermont, Florida · 16-Agent Boutique", "Winter Park, Florida · Boutique Luxury"),
    ('<h1 class="practice-name">Sunbright Realty</h1>',
     '<h1 class="practice-name">Palmano Group</h1>'),
    ('<p class="practice-doctor">Lou Salvemini Jr., Broker/Owner</p>',
     '<p class="practice-doctor">Richard Palmano, Broker</p>'),
    ("<h4>16 Agents, One Number, Always Open</h4>",
     "<h4>Concierge for Luxury Buyers and Sellers</h4>"),
    ("Whether it's a Saturday-night Zillow scroll or a Sunday open-house follow-up, Lou and the Sunbright team are committed to capturing every lead in real time — even when one of the 16 agents is mid-closing.",
     "The luxury buyer doesn't browse Zillow at 9pm — they research a specific property or neighborhood and expect a considered conversation. Richard's commitment is to be the broker who actually responds with the kind of conversation that level of buyer expects."),
    ("1825 East Hwy 50, Suite 100<br>Clermont, FL 34711",
     "150 N Orlando Ave, Suite 200<br>Winter Park, FL 32789"),
    ("(352) 536-3714", "(407) 232-5801"),
    ("<strong>Sunbright Concierge</strong> · Available 24/7",
     "<strong>Palmano Concierge</strong> · Available 24/7"),
    ("Already working with a Sunbright agent? They'll be notified directly for active deals.",
     "Already working with Richard? He'll be notified directly for active deals."),
    ("Welcome to Sunbright Realty. I'm the after-hours concierge for Lou and the team — I can answer most questions, qualify what you're looking for, and route you to the right agent. The Sunbright team handles Lake County, Clermont, Minneola, and Groveland markets.",
     "Welcome to Palmano Group. I'm Richard's after-hours concierge — I can answer most questions, walk you through specific properties, and qualify what you're looking for. Palmano specializes in luxury homes throughout Winter Park, Maitland, and the Orlando luxury corridor."),
    # Buyer language → luxury
    ("Great — Sunbright is one of Lake County's most active boutique brokerages, with 16 agents covering Clermont, Minneola, Groveland, and the Four Corners. The market moves fast right now, so the more I can lock down tonight, the more aggressive your agent can be on Monday morning.",
     "Great — Richard's specialty is the luxury market in Winter Park and the Orlando luxury corridor. The luxury inventory is thinner and moves on different timing than the broader market, so the more I understand about what you're looking for tonight, the more targeted Richard can be tomorrow."),
    ("Perfect — Sunbright works with several preferred local lenders who specialize in Florida buyers, including some who routinely close in under 30 days. Lou's team will introduce you to the right one based on your situation. Most buyers save weeks doing it this way.",
     "Perfect — Richard works with several private lenders who specialize in luxury buyers and jumbo financing. They handle non-conforming loans, foreign buyers, and complex income situations that retail lenders fumble. Most luxury buyers save weeks doing it this way."),
    ("`No pressure at all — most of Sunbright's best clients started exactly here. Lou or one of the 16 agents will meet you where you are: zero-pressure 30-minute sit-down to map out Lake County neighborhoods, price ranges, and what pre-approval looks like when you're ready.<br><br>Want to lock that in this week or next?`",
     "`No pressure at all — luxury buyers often spend a year quietly looking before they engage an agent. Richard's a great person to talk to early because he doesn't push — he's a 30-minute meeting to walk through Winter Park / Maitland inventory, price ranges, and what pre-approval looks like when you're ready.<br><br>Want to lock that in this week or next?`"),
    ("Got it — Lou keeps Tuesday afternoons clear specifically for buyers who need to move fast in the Lake County market.",
     "Got it — Richard keeps Tuesday and Thursday afternoons open specifically for luxury buyers who need to move fast."),
    ("Solid timeline — Sunbright's planning meetings are perfect for that horizon.",
     "Solid timeline — Richard's planning meetings are perfect for that horizon."),
    ("Smart to start early — gives the Sunbright team time to learn what you actually want, not just what the search filters say.",
     "Smart to start early — gives Richard time to learn what you actually want, including off-market inventory that doesn't show up on search filters."),
    ("Sunbright is one of Lake County's most active brokerages — 16 agents who actually know the local micro-markets. The two questions every seller asks first: <em>\"What's it worth?\"</em> and <em>\"How fast can it move?\"</em><br><br>Both get answered properly in a 60-minute listing consultation at your home — your Sunbright agent walks the property, pulls comps, and gives you a real strategy. Free, no obligation. What's your timeline?",
     "Selling luxury is its own discipline — most agents under-price luxury homes because they don't have comps for properties that rarely trade. Richard's brokerage focuses on luxury specifically. The two questions every luxury seller asks first: <em>\"What's the right number?\"</em> and <em>\"Who's the right buyer?\"</em><br><br>Both get answered properly in a 60-minute listing consultation at your home — Richard walks the property, pulls real luxury comps, and gives you a real strategy. Free, no obligation. What's your timeline?"),
    ("Understood — life moves fast sometimes. Your Sunbright agent can be at your door this week with comps in hand.",
     "Understood — Richard can be at your door this week with comps and a positioning strategy."),
    ("Perfect timeline — Sunbright can plan the staging and listing strategy properly with that runway.",
     "Perfect timeline — Richard can plan the staging, photography, and luxury-buyer positioning properly with that runway."),
    ("Smart to know your number before deciding — your Sunbright agent will give you an honest valuation, not a hype number.",
     "Smart to know your number before deciding — Richard will give you an honest luxury valuation, not a hype number."),
    # First-time buyer doesn't really apply for luxury — modify
    ("First-time buyer programs in Lake County are bigger than most people realize — there are state and county programs that combine to make $0-down-on-paper deals possible for qualified buyers. Sunbright works with lenders who specialize in these. Lou personally walks first-time buyers through it.",
     "First-time luxury buyers face a different challenge than the typical first-timer — usually it's financing structure (jumbo, foreign income, asset-based) and understanding what differentiates luxury inventory from over-priced traditional homes. Richard walks first-time luxury buyers through this personally."),
    ("`Of course — type your question and I'll do my best. If it's something Lou or your assigned agent needs to weigh in on personally (offer strategy, contract details, Lake County specifics), I'll route it to them and someone will get back to you in the morning.`",
     "`Of course — type your question and I'll do my best. If it's something Richard needs to weigh in on personally (specific properties, offer strategy, neighborhood specifics), I'll route it to him and he'll get back to you in the morning.`"),
    ("Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Lou's calendar?",
     "Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Richard's calendar?"),
    ('<div class="booking-icon">S</div>', '<div class="booking-icon">P</div>'),
    ('<span class="value">Lou Salvemini Jr.</span>', '<span class="value">Richard Palmano</span>'),
    ('<span class="value">1825 East Hwy 50, Clermont</span>',
     '<span class="value">150 N Orlando Ave, Winter Park</span>'),
    ("(352) 536-3714", "(407) 232-5801"),
    ("Lou or your assigned agent will text a confirmation by 9 AM.",
     "Richard will text you a confirmation by 9 AM."),
    ("The team wants to pull comps before the visit.", "Richard wants to pull comps before the visit."),
    ("Lou will reach out", "Richard will reach out"),
    ("Lou has been notified", "Richard has been notified"),
    ("`No problem. Lou has openings", "`No problem. Richard has openings"),
    ("(352) 536-3714", "(407) 232-5801"),  # in case missed
    ("sunbrightrealty.com", "palmanogroup.com"),
    ("Sunbright preferred lenders", "private luxury lenders"),
]

PALMANO_CLEANUP = [
    ("Lou Salvemini Jr.", "Richard Palmano"),
    ("Lou", "Richard"),
    ("Sunbright Realty", "Palmano Group"),
    ("Sunbright", "Palmano"),
    ("Clermont", "Winter Park"),  # in case missed
    ("Lake County", "the Orlando luxury corridor"),
]

# ============================================================================
# BATCH 2 — 7 more prospects from xlsx
# ============================================================================

# ---- NAMI — Michelin Japanese omakase, Lake Nona (uses kadence.html base) ----
NAMI_SUBS = [
    ("Kadence — Omakase Reservations Concierge | Powered by Velo AI",
     "Nami — Omakase Reservations Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Kadence.",
     "This is a live demo built by Velo AI for Nami."),
    ("Audubon Park, Orlando · 1 Michelin Star",
     "Lake Nona, Orlando · Michelin-Recognized Omakase"),
    ('<h1 class="practice-name">Kadence</h1>',
     '<h1 class="practice-name">Nami</h1>'),
    ('<p class="practice-doctor">The Kadence Team</p>',
     '<p class="practice-doctor">The Nami Team</p>'),
    ("Kadence runs a 9-seat omakase counter where the chefs can't pause for the phone — but reservation requests, waitlist inquiries, and dietary considerations get captured around the clock.",
     "Nami runs an intimate omakase service where the chefs can't pause for the phone — but reservation requests, waitlist inquiries, and dietary considerations get captured around the clock."),
    ("1809 Winter Park Rd<br>Orlando, FL 32803",
     "6925 Lake Nona Blvd, Suite 100<br>Lake Nona, FL 32827"),
    ("(407) 270-6997", "(407) 395-4857"),
    ("<strong>Kadence Concierge</strong> · Available 24/7",
     "<strong>Nami Concierge</strong> · Available 24/7"),
    ("Welcome to Kadence. We're a 9-seat omakase counter, so service is intimate and the chefs can't pause to answer the phone. I'm here to take reservation requests, manage the waitlist, walk through dietary considerations, and route anything special to the team.",
     "Welcome to Nami. Service is intimate and the chefs can't pause to answer the phone — but I'm here to take reservation requests, manage the waitlist, walk through dietary considerations, and route anything special to the team."),
    ("Of course — Kadence often has last-minute openings due to cancellations. I can add you to tonight's or this week's waitlist with priority based on flexibility. Tell me your party size and which night(s) work, and I'll text you immediately if a seat opens up.",
     "Of course — Nami regularly has last-minute openings due to cancellations. I can add you to tonight's or this week's waitlist with priority based on flexibility. Tell me your party size and which night(s) work, and I'll text you the moment a seat opens up."),
    ("Buyouts at Kadence are unique — the entire 9-seat counter for one party, custom omakase progression. The chefs love planning these. What's the occasion?",
     "Buyouts at Nami are unique — the entire counter for your party, custom omakase progression. The chefs love planning these. What's the occasion?"),
    ("Of course — Kadence is a 12-course omakase, so dietary accommodations need to be planned in advance. The team handles most allergens (shellfish, gluten, sesame) and can craft a fully vegan or pescatarian progression with 48hrs notice. What's the consideration?",
     "Of course — Nami is a multi-course omakase, so dietary accommodations need to be planned in advance. The team handles most allergens (shellfish, gluten, sesame) and can craft a fully vegan or pescatarian progression with 48hrs notice. What's the consideration?"),
    ("(407) 270-6997", "(407) 395-4857"),
    ('<div class="booking-icon">K</div>', '<div class="booking-icon">N</div>'),
    ('<span class="value">Kadence Team</span>', '<span class="value">Nami Team</span>'),
    ('<span class="value">1809 Winter Park Rd, Orlando</span>',
     '<span class="value">6925 Lake Nona Blvd, Lake Nona</span>'),
    ("Kadence", "Nami"),
]
NAMI_CLEANUP = [("kadenceorlando.com", "namilakenona.com")]

# ---- CORO — Spanish tapas Michelin, Audubon Park (uses bacan.html base) ----
CORO_SUBS = [
    ("BACÁN — Reservations & Private Dining Concierge | Powered by Velo AI",
     "Coro — Reservations & Tapas Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for BACÁN at Lake Nona Wave Hotel.",
     "This is a live demo built by Velo AI for Coro Restaurant."),
    ("Lake Nona, FL · Michelin-Recognized", "Audubon Park, Orlando · Michelin Spanish Tapas"),
    ('<h1 class="practice-name">BACÁN</h1>', '<h1 class="practice-name">Coro</h1>'),
    ('<p class="practice-doctor">Chef Guillaume Robin</p>',
     '<p class="practice-doctor">The Coro Team</p>'),
    ("BACÁN runs a refined dinner service where the team can't always pause to answer the phone — but reservations, dietary inquiries, and private dining requests get captured around the clock.",
     "Coro runs a refined Spanish tapas service where the team can't always pause to answer the phone — but reservations, dietary inquiries, and private events get captured around the clock."),
    ("6500 Tavistock Lakes Blvd<br>Lake Nona, FL 32827",
     "3201 Corrine Dr, Suite 100<br>Orlando, FL 32803"),
    ("(407) 675-2000", "(407) 629-5005"),
    ("<strong>BACÁN Concierge</strong> · Available 24/7",
     "<strong>Coro Concierge</strong> · Available 24/7"),
    ("Hotel guest or private dining inquiry? Chef Robin's team is notified directly.",
     "Private event or large-party inquiry? The Coro team is notified directly."),
    ("Welcome to BACÁN. The dining room is mid-service and the team can't always pick up — but I'm here. I can take reservations, scope private dining, walk you through dietary considerations, and have anything time-sensitive in front of Chef Robin before service tomorrow.",
     "Welcome to Coro. The dining room is mid-service and the team can't always pick up — but I'm here. I can take reservations, scope private events, walk you through the tapas menu and dietary options, and route anything time-sensitive to the team."),
    ("Private dining at BACÁN can accommodate intimate dinners up to full restaurant buyouts for hotel events. What kind of event are you considering?",
     "Private dining at Coro accommodates intimate dinners up to full restaurant buyouts. What kind of event are you considering?"),
    ("Private dining at BACÁN starts at parties of 8 with a curated tasting menu, and scales to full restaurant buyouts. Pricing is typically $125-225 per person depending on the menu and beverage program. Chef Robin's team does a planning call before quoting — that way the menu fits the event, not the other way around.",
     "Private dining at Coro starts at parties of 8 with a curated tapas progression, and scales to full restaurant buyouts. Pricing is typically $85-145 per person depending on the menu and beverage program. The team does a planning call before quoting so the menu actually fits the event."),
    ("Welcome — are you a Lake Nona Wave Hotel guest looking to book at BACÁN? I can hold a table prioritized for hotel guests, walk through the menu, or answer hours and dress code questions. What can I help with?",
     "Of course — type your question. Hours, the tapas menu, dietary stuff (the kitchen handles vegetarian and gluten-free with notice), or anything specific to a dish — I can usually answer right now."),
    ("(407) 675-2000", "(407) 629-5005"),
    ('<div class="booking-icon">B</div>', '<div class="booking-icon">C</div>'),
    ('<span class="value">BACÁN Team</span>', '<span class="value">Coro Team</span>'),
    ('<span class="value">6500 Tavistock Lakes Blvd, Lake Nona</span>',
     '<span class="value">3201 Corrine Dr, Orlando</span>'),
    ("Chef Robin", "the Coro team"),
    ("BACÁN", "Coro"),
]
CORO_CLEANUP = [("bacanlakenona.com", "cororestaurant.com")]

# ---- THE LOOK SALON & SPA — Oviedo full-service (uses goldie.html) ----
THELOOK_SUBS = [
    ("Goldie Salon — After-Hours Booking Concierge | Powered by Velo AI",
     "The Look Salon & Spa — Booking Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Goldie Salon.",
     "This is a live demo built by Velo AI for The Look Salon & Spa."),
    ("Lake Mary, Florida · Luxury Hair", "Oviedo, Florida · Hair & Spa"),
    ('<h1 class="practice-name">Goldie Salon</h1>',
     '<h1 class="practice-name">The Look Salon &amp; Spa</h1>'),
    ('<p class="practice-doctor">The Goldie Team</p>',
     '<p class="practice-doctor">The Look Team</p>'),
    ("Goldie's stylists are committed to giving every client a seamless experience — from the first DM at 11pm to the final blowout. The booking line never sleeps.",
     "The Look's full-service team handles hair, spa, and skincare under one roof — from the first booking inquiry at 11pm to the final treatment. The booking line never sleeps."),
    ("1010 W Lake Mary Blvd<br>Lake Mary, FL 32746",
     "151 Geneva Dr, Suite 1006<br>Oviedo, FL 32765"),
    ("(321) 363-1233", "(407) 977-8481"),
    ("<strong>Goldie Concierge</strong> · Available 24/7",
     "<strong>The Look Concierge</strong> · Available 24/7"),
    ("A regular at Goldie? Your stylist will be notified directly for time-sensitive bookings.",
     "A regular at The Look? Your stylist will be notified directly for time-sensitive bookings."),
    ("Welcome to Goldie. Your stylist's chair is empty for the night, but I'm the after-hours booking concierge — I can quote services, hold appointments, and answer most questions before you go to sleep.",
     "Welcome to The Look. The salon and spa are wrapped for the night, but I'm here — I can quote services across hair, color, skincare, and spa, hold appointments, and answer most questions before you go to sleep."),
    ('<div class="booking-icon">G</div>', '<div class="booking-icon">L</div>'),
    ('<span class="value">Goldie Stylist</span>', '<span class="value">The Look Stylist</span>'),
    ('<span class="value">1010 W Lake Mary Blvd</span>',
     '<span class="value">151 Geneva Dr, Oviedo</span>'),
    ("(321) 363-1233", "(407) 977-8481"),
    ("Goldie", "The Look"),
]
THELOOK_CLEANUP = []

# ---- LATHAM LUNA — Business / bankruptcy / construction law, Orlando ----
LATHAMLUNA_SUBS = [
    ("Lance A. Ragland, P.A. — After-Hours Intake | Powered by Velo AI",
     "Latham Luna — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Lance A. Ragland, P.A.",
     "This is a live demo built by Velo AI for Latham Luna"),
    ("Winter Springs, Florida · Est. 2015", "Orlando, Florida · Business Law"),
    ('<h1 class="practice-name">Lance A. Ragland, P.A.</h1>',
     '<h1 class="practice-name">Latham Luna</h1>'),
    ('<p class="practice-doctor">Lance A. Ragland, Esq.</p>',
     '<p class="practice-doctor">Daniel Velasquez, Esq.</p>'),
    ("<h4>Available When You Need Him</h4>", "<h4>Business Law With Real Bandwidth</h4>"),
    ("Estate matters rarely surface during business hours. Lance is committed to being there for clients during life's most difficult transitions. You're never alone.",
     "Business matters rarely surface during business hours — vendor disputes hit Friday at 6pm, foreclosure deadlines fall on weekends, lien questions come in at midnight. Daniel is committed to being available when business actually moves."),
    ("5750 Canton Cove<br>Winter Springs, FL 32708",
     "111 N Magnolia Ave, Suite 1400<br>Orlando, FL 32801"),
    ("(407) 960-6069", "(407) 481-5800"),
    ("By Appointment · Mon–Fri 9a–5p", "Mon–Fri 9a–5p · Confidential"),
    ("<strong>Ragland Intake</strong> · Available 24/7",
     "<strong>Latham Luna Intake</strong> · Available 24/7"),
    ("A current client of Lance's? He'll be notified directly for urgent matters.",
     "A current client? Daniel will be notified directly for urgent matters."),
    ("Good evening — you've reached the after-hours line for the Law Offices of Lance A. Ragland. Lance focuses entirely on estate planning, probate, and trust matters. He's unavailable right now, but I can take down what's on your mind and get him to reach back out.",
     "Good evening — you've reached the after-hours line for Latham Luna. Daniel handles business law, bankruptcy, and construction matters — vendor disputes, contract enforcement, foreclosure defense, mechanic's liens. He's wrapped for the day, but I can take down what's going on and get him back to you fast."),
    ("{ label: '🕯️ I lost a loved one', value: 'probate' },\n        { label: '📜 Plan a will or trust', value: 'planning' },\n        { label: '🏥 Power of attorney / healthcare', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }",
     "{ label: '💼 Business / contract dispute', value: 'probate' },\n        { label: '🏗️ Construction lien or claim', value: 'planning' },\n        { label: '📉 Bankruptcy or foreclosure', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }"),
    ("'probate': \"I lost a loved one and need probate help\",\n      'planning': \"I'd like to plan a will or trust\",\n      'poa': \"I need a power of attorney or healthcare paperwork\"",
     "'probate': \"I have a business or contract dispute\",\n      'planning': \"I have a construction lien or claim\",\n      'poa': \"I have a bankruptcy or foreclosure question\""),
    ("if (value === 'probate') {\n      memory.matter = 'probate';\n      await addBotMessage(\n        `I'm so sorry for your loss. Please take whatever time you need.<br><br>Lance has guided families through probate for nearly thirty years, and most of what feels overwhelming right now has a clear path forward. The two things that help him move quickly when he calls you back: who passed, and whether they had a will.`,",
     "if (value === 'probate') {\n      memory.matter = 'business';\n      await addBotMessage(\n        `Business disputes are exactly what Daniel handles every week — non-payment, breach of contract, vendor disputes, partner disagreements. The two things that help him move fast: what's the dispute, and whether there's a deadline (court date, contract clause, payment deadline) anywhere in the next two weeks.`,"),
    ("`If you're able to share — who is this for?`,\n        900,\n        [\n          { label: 'Spouse', value: 'spouse' },\n          { label: 'Parent', value: 'parent' },\n          { label: 'Other family member', value: 'other-family' }\n        ]",
     "`First — what kind of dispute?`,\n        900,\n        [\n          { label: 'Vendor / contract dispute', value: 'spouse' },\n          { label: 'Partner / shareholder', value: 'parent' },\n          { label: 'Customer / receivables', value: 'other-family' }\n        ]"),
    ("'spouse': \"My spouse\",\n      'parent': \"A parent\",\n      'other-family': \"Another family member\"",
     "'spouse': \"Vendor or contract dispute\",\n      'parent': \"Partner or shareholder issue\",\n      'other-family': \"Customer / collections issue\""),
    ("if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.relation = value;\n      await addBotMessage(\n        `Thank you. Did they have a will or any estate documents in place?`,",
     "if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.disputeType = value;\n      await addBotMessage(\n        `Thank you. Is there a written contract or agreement in place?`,"),
    ("[\n          { label: 'Yes, they had a will', value: 'has-will' },\n          { label: 'No', value: 'no-will' },\n          { label: \"I'm not sure\", value: 'unsure-will' }\n        ]",
     "[\n          { label: 'Yes, signed contract', value: 'has-will' },\n          { label: 'Verbal / handshake only', value: 'no-will' },\n          { label: \"I'm not sure\", value: 'unsure-will' }\n        ]"),
    ("memory.hasWill = value;\n      await addBotMessage(\n        `Got it. One more question, then I'll get this in front of Lance — is anything time-pressured? Sometimes accounts get frozen, or a property has a deadline. Other times there's just no rush.`,",
     "memory.hasContract = value;\n      await addBotMessage(\n        `Got it. One more question — is there a deadline coming (court date, demand letter response, contractual notice period)?`,"),
    ("'urgent-frozen': \"Yes — accounts are frozen / property at risk\",\n      'urgent-soon': \"Soon, but not in crisis\",\n      'urgent-planning': \"No urgency — just planning ahead\"",
     "'urgent-frozen': \"Yes — deadline within 7 days\",\n      'urgent-soon': \"Within 30 days\",\n      'urgent-planning': \"No deadline\""),
    ("[\n          { label: '🔴 Yes — accounts frozen / property at risk', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not in crisis', value: 'urgent-soon' },\n          { label: '🟢 No urgency — just planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Deadline within 7 days', value: 'urgent-frozen' },\n          { label: '🟡 Within 30 days', value: 'urgent-soon' },\n          { label: '🟢 No deadline', value: 'urgent-planning' }\n        ]"),
    ("`Understood — that's exactly the kind of thing Lance wants to know about right away. I'm flagging this as priority and Lance will call you first thing tomorrow morning, before his appointments start.<br><br>Can I get your first name and best callback number? If a deadline is in the next 48 hours, please mention it.`",
     "`Understood — Daniel wants to hear about urgent business matters tonight if there's a real deadline. I'm flagging this as priority and he'll call you within the hour during business hours, or first thing in the morning if it's late tonight.<br><br>Can I get your first name and best callback number? Please mention if the deadline is in the next 48 hours.`"),
    ("`Thank you — that helps. Lance opens his calendar Tuesday through Thursday for new probate matters and sets aside ninety minutes per consultation so nothing feels rushed.<br><br>What's your first name? I'll have him reach out by mid-morning to set a time that works.`",
     "`Thank you — that helps. Daniel keeps consultation slots Tuesday through Thursday for new business matters. He's been practicing for over fifteen years across business, bankruptcy, and construction — the consult is where he tells you straight whether you have a case worth pursuing.<br><br>What's your first name? I'll have him reach out tomorrow morning.`"),
    ("if (value === 'planning') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart of you to think about this — most people put off estate planning for years and regret the procrastination. Lance has been doing wills, trusts, and estate plans exclusively since 2015, so this is exactly his bread and butter.<br><br>Most clients in your shoes are weighing one of two things: <em>\"Do I just need a will, or do I need a trust?\"</em> and <em>\"What's this going to cost me?\"</em><br><br>Both are answered properly in a one-hour consult — Lance reviews your situation, walks you through the difference, and gives you a flat-fee quote before you commit to anything. Want me to hold a slot this week or next?`,",
     "if (value === 'planning') {\n      memory.matter = 'construction';\n      await addBotMessage(\n        `Construction matters move on tight statutory deadlines — mechanic's liens, notice to owner timing, payment bond claims. Daniel handles construction law specifically and the first thing he checks is whether you're inside the deadline window.<br><br>Most callers are weighing two things: <em>\"Did I miss the lien deadline?\"</em> and <em>\"Is the dispute worth the legal cost?\"</em><br><br>Both get answered in a 30-minute consult. Want me to hold a slot this week or next?`,"),
    ("if (value === 'poa') {\n      memory.matter = 'poa';\n      await addBotMessage(\n        `These conversations are hard — usually they come up because someone in the family is going through a health change. Lance can put together a power of attorney and healthcare surrogate quickly, often within a few days if needed.<br><br>Just so I get the right urgency to him: is this for an immediate situation, or planning ahead?`,",
     "if (value === 'poa') {\n      memory.matter = 'bankruptcy';\n      await addBotMessage(\n        `Bankruptcy and foreclosure timing matters — there are filing windows, automatic stays, and hearing dates that can't slip. Daniel handles both consumer and small-business bankruptcy plus foreclosure defense. The first thing he wants to know is the urgency.<br><br>Where are you on the timeline?`,"),
    ("[\n          { label: '🔴 Immediate — health is declining', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not crisis', value: 'urgent-soon' },\n          { label: '🟢 Planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Foreclosure / lawsuit served', value: 'urgent-frozen' },\n          { label: '🟡 Falling behind, no lawsuit yet', value: 'urgent-soon' },\n          { label: '🟢 Just exploring options', value: 'urgent-planning' }\n        ]"),
    ("`Of course — go ahead and type your question. If it's something Lance needs to weigh in on personally, I'll route it to him and he'll get back to you in the morning. If it's something I can answer from his practice info, I'll do my best.`",
     "`Of course — type your question. If it's something Daniel needs to weigh in on personally (case strategy, opposing counsel, statutory specifics), I'll route it to him and he'll get back to you in the morning.`"),
    ('<div class="booking-icon">L</div>', '<div class="booking-icon">L</div>'),
    ('<span class="value">Lance A. Ragland, Esq.</span>',
     '<span class="value">Daniel Velasquez, Esq.</span>'),
    ('<span class="value">5750 Canton Cove, Winter Springs</span>',
     '<span class="value">111 N Magnolia Ave, Orlando</span>'),
    ("'planning': 'Estate Planning Consultation',\n          'poa': 'Power of Attorney Consultation',\n          'probate': 'Probate Consultation',\n          'question': 'General Consultation'",
     "'business': 'Business Dispute Consultation',\n          'construction': 'Construction Law Consultation',\n          'bankruptcy': 'Bankruptcy / Foreclosure Consultation',\n          'question': 'General Consultation'"),
    ("(407) 960-6069", "(407) 481-5800"),
    ("Lance has been notified", "Daniel has been notified"),
    ("Lance will reach out", "Daniel will reach out"),
    ("Lance opens new-patient slots Tuesday through Thursday",
     "Daniel opens consultation slots Tuesday through Thursday"),
    ("`No problem. Lance has openings", "`No problem. Daniel has openings"),
    ("Lance ", "Daniel "),
    ("Lance's", "Daniel's"),
    ("Lance.", "Daniel."),
    ("Lance,", "Daniel,"),
    ("his office (Debbie)", "his office"),
]
LATHAMLUNA_CLEANUP = [("Lance", "Daniel"), ("Ragland", "Latham Luna")]

# ---- MURPHY & BERGLUND — Estate + family + elder law (uses velizkatz.html) ----
MURPHYBERGLUND_SUBS = [
    ("Veliz Katz Law — After-Hours Intake | Powered by Velo AI",
     "Murphy & Berglund — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Veliz Katz Law",
     "This is a live demo built by Velo AI for Murphy & Berglund"),
    ("Maitland, Florida · Family + Estate", "Altamonte Springs, Florida · Estate &amp; Elder Law"),
    ('<h1 class="practice-name">Veliz Katz Law</h1>',
     '<h1 class="practice-name">Murphy &amp; Berglund</h1>'),
    ('<p class="practice-doctor">David Veliz &amp; Norberto Katz, Esq.</p>',
     '<p class="practice-doctor">Michelle Berglund-Harper &amp; Jodi Murphy, Esq.</p>'),
    ("Family law and estate planning both surface during life's hardest moments — divorce, custody, the death of a parent. David and Norberto are committed to being there during those transitions. You're never alone.",
     "Estate planning, elder law, and family matters all surface during life's hardest transitions — declining health, the death of a parent, a Medicaid crisis. Michelle and Jodi are committed to being there during those moments. You're never alone."),
    ("1936 Lee Rd<br>Maitland, FL 32751",
     "961 N Hunt Club Rd<br>Altamonte Springs, FL 32714"),
    ("(407) 849-7072", "(407) 539-4040"),
    ("<strong>Veliz Katz Intake</strong> · Available 24/7",
     "<strong>Murphy &amp; Berglund Intake</strong> · Available 24/7"),
    ("A current client? David or Norberto will be notified directly for urgent matters.",
     "A current client? Michelle or Jodi will be notified directly for urgent matters."),
    ("Good evening — you've reached the after-hours line for Veliz Katz Law. The firm handles family law and estate planning — divorce, custody, probate, and trust matters. Both attorneys are wrapped for the day, but everything you share with me is confidential. I'll take down what's on your mind and get the right attorney to reach back out.",
     "Good evening — you've reached the after-hours line for Murphy & Berglund. The firm handles estate planning, elder law, family law, and probate. Both attorneys are wrapped for the day, but everything you share is confidential. I'll take down what's on your mind and get the right attorney to reach back out."),
    ("{ label: '💔 Family law / divorce / custody', value: 'probate' },\n        { label: '🕯️ Estate / probate matter', value: 'planning' },\n        { label: '📜 Wills and trusts', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }",
     "{ label: '🕯️ Estate / probate matter', value: 'probate' },\n        { label: '👵 Elder law / Medicaid', value: 'planning' },\n        { label: '📜 Wills and trusts', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }"),
    ("'probate': \"I have a family law matter\",\n      'planning': \"I lost a loved one or need probate help\",\n      'poa': \"I want to plan a will or trust\"",
     "'probate': \"I lost a loved one or need probate help\",\n      'planning': \"I have an elder law / Medicaid question\",\n      'poa': \"I want to plan a will or trust\""),
    # Family path → estate (probate)
    ("if (value === 'probate') {\n      memory.matter = 'family';\n      await addBotMessage(\n        `Family law matters are some of the most personal calls a firm receives. David handles family law specifically, and the firm has helped clients through divorce, custody disputes, and modifications for over twenty years. The two things that help David move quickly: what's the situation, and whether kids are involved.`,",
     "if (value === 'probate') {\n      memory.matter = 'estate';\n      await addBotMessage(\n        `I'm sorry — these calls are usually placed at one of the hardest moments. Jodi handles probate at the firm, including the post-loss paperwork most families don't know how to navigate. The two things that help her move quickly: who passed, and whether they had any documents in place.`,"),
    ("`If you're able to share — what's the situation?`,\n        900,\n        [\n          { label: 'Considering divorce', value: 'spouse' },\n          { label: 'Custody dispute', value: 'parent' },\n          { label: 'Modification or post-decree', value: 'other-family' }\n        ]",
     "`If you're able to share — who is this for?`,\n        900,\n        [\n          { label: 'Spouse', value: 'spouse' },\n          { label: 'Parent', value: 'parent' },\n          { label: 'Other family member', value: 'other-family' }\n        ]"),
    ("'spouse': \"Considering divorce\",\n      'parent': \"Custody dispute\",\n      'other-family': \"Modification matter\"",
     "'spouse': \"My spouse\",\n      'parent': \"A parent\",\n      'other-family': \"Another family member\""),
    ("if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.situation = value;\n      await addBotMessage(\n        `Thank you. Are children involved?`,\n        900,\n        [\n          { label: 'Yes, with custody concerns', value: 'has-will' },\n          { label: 'Yes, but no current dispute', value: 'no-will' },\n          { label: 'No children', value: 'unsure-will' }\n        ]\n      );\n      return;\n    }",
     "if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.relation = value;\n      await addBotMessage(\n        `Thank you. Did they have a will or any estate documents in place?`,\n        900,\n        [\n          { label: 'Yes, they had a will', value: 'has-will' },\n          { label: 'No', value: 'no-will' },\n          { label: \"I'm not sure\", value: 'unsure-will' }\n        ]\n      );\n      return;\n    }"),
    # Planning path → elder law
    ("if (value === 'planning') {\n      memory.matter = 'estate';\n      await addBotMessage(\n        `I'm sorry — these calls are usually placed at one of the hardest moments. Norberto handles estate matters at the firm, including probate, trust administration, and the post-loss paperwork most families don't know how to navigate. The two things that help him move quickly: who passed, and whether they had any documents in place.<br><br>Want me to set up a confidential consultation this week or next?`,",
     "if (value === 'planning') {\n      memory.matter = 'elder';\n      await addBotMessage(\n        `Elder law calls usually surface around two specific events: a parent's care needs are escalating, or a Medicaid eligibility question just got real. Michelle handles elder law specifically — long-term care planning, asset protection, Medicaid qualification, guardianship.<br><br>What's driving the call?`,"),
    # POA path → wills and trusts (already estate planning structure)
    ("if (value === 'poa') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart to think about this before you need it — most people put off estate planning until a crisis forces the conversation, which is exactly the wrong time. Norberto can put together wills, trusts, powers of attorney, and healthcare surrogates as a coordinated package.<br><br>Just so I route the right urgency: is this for planning ahead, or is something immediate driving the timing?`,",
     "if (value === 'poa') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart to think about this before you need it — most people put off estate planning until a crisis forces the conversation, which is exactly the wrong time. Jodi puts together wills, trusts, powers of attorney, and healthcare surrogates as a coordinated package.<br><br>Just so I route the right urgency: is this for planning ahead, or is something immediate driving the timing?`,"),
    ("`Of course — type your question. The firm handles family law (David) and estate planning (Norberto), so I'll route it to whoever it fits best.`",
     "`Of course — type your question. The firm handles estate planning, probate, elder law, and family law, so I'll route it to whichever attorney fits best.`"),
    ('<div class="booking-icon">V</div>', '<div class="booking-icon">M</div>'),
    ('<span class="value">David Veliz or Norberto Katz, Esq.</span>',
     '<span class="value">Michelle Berglund-Harper or Jodi Murphy, Esq.</span>'),
    ('<span class="value">1936 Lee Rd, Maitland</span>',
     '<span class="value">961 N Hunt Club Rd, Altamonte Springs</span>'),
    ("'estate': 'Estate / Probate Consultation',\n          'planning': 'Estate Planning Consultation',\n          'family': 'Family Law Consultation',\n          'question': 'General Consultation'",
     "'estate': 'Probate Consultation',\n          'planning': 'Estate Planning Consultation',\n          'elder': 'Elder Law / Medicaid Consultation',\n          'question': 'General Consultation'"),
    ("(407) 849-7072", "(407) 539-4040"),
    ("The Veliz Katz team", "Michelle and Jodi"),
    ("the Veliz Katz attorneys", "Michelle and Jodi"),
    ("David ", "Michelle "),
    ("Norberto", "Jodi"),
    ("Maitland", "Altamonte Springs"),
]
MURPHYBERGLUND_CLEANUP = [
    ("Veliz Katz", "Murphy & Berglund"),
    ("velizkatzlaw.com", "murphyberglund.com"),
]

# ---- THE FUNK COLLECTION — Luxury RE, eXp, Windermere (uses palmano.html) ----
FUNK_SUBS = [
    ("Palmano Group — Luxury RE Concierge | Powered by Velo AI",
     "The Funk Collection — Luxury RE Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Palmano Group.",
     "This is a live demo built by Velo AI for The Funk Collection."),
    ("Winter Park, Florida · Boutique Luxury", "Windermere, Florida · Luxury Estates"),
    ('<h1 class="practice-name">Palmano Group</h1>',
     '<h1 class="practice-name">The Funk Collection</h1>'),
    ('<p class="practice-doctor">Richard Palmano, Broker</p>',
     '<p class="practice-doctor">Jeffrey &amp; Renee Funk</p>'),
    ("The luxury buyer doesn't browse Zillow at 9pm — they research a specific property or neighborhood and expect a considered conversation. Richard's commitment is to be the broker who actually responds with the kind of conversation that level of buyer expects.",
     "The luxury estate buyer doesn't browse Zillow at 9pm — they research specific properties on private golf communities and waterfront lots, and expect a considered conversation. The Funks' commitment is to respond with the kind of conversation Windermere luxury actually demands."),
    ("150 N Orlando Ave, Suite 200<br>Winter Park, FL 32789",
     "11550 Bridge House Rd, Suite 200<br>Windermere, FL 34786"),
    ("(407) 232-5801", "(407) 438-4028"),
    ("<strong>Palmano Concierge</strong> · Available 24/7",
     "<strong>Funk Concierge</strong> · Available 24/7"),
    ("Already working with Richard? He'll be notified directly for active deals.",
     "Already working with Jeffrey or Renee? They'll be notified directly for active deals."),
    ("Welcome to Palmano Group. I'm Richard's after-hours concierge — I can answer most questions, walk you through specific properties, and qualify what you're looking for. Palmano specializes in luxury homes throughout Winter Park, Maitland, and the Orlando luxury corridor.",
     "Welcome to The Funk Collection. I'm the after-hours concierge for Jeffrey and Renee — I can answer most questions, walk you through specific properties, and qualify what you're looking for. The Funks specialize in luxury estates in Windermere, Isleworth, and the gated communities around Lake Butler."),
    ("Great — Richard's specialty is the luxury market in Winter Park and the Orlando luxury corridor. The luxury inventory is thinner and moves on different timing than the broader market, so the more I understand about what you're looking for tonight, the more targeted Richard can be tomorrow.",
     "Great — the Funks' specialty is luxury estates in Windermere, Isleworth, and the surrounding gated communities. Inventory is thinner at this level and moves on different timing than the broader market, so the more I understand tonight, the more targeted they can be tomorrow."),
    ("Perfect — Richard works with several private lenders who specialize in luxury buyers and jumbo financing. They handle non-conforming loans, foreign buyers, and complex income situations that retail lenders fumble. Most luxury buyers save weeks doing it this way.",
     "Perfect — the Funks work with several private lenders who specialize in luxury buyers and jumbo financing. They handle non-conforming loans, foreign buyers, and complex income situations that retail lenders fumble. Most luxury buyers save weeks doing it this way."),
    ("`No pressure at all — luxury buyers often spend a year quietly looking before they engage an agent. Richard's a great person to talk to early because he doesn't push — he's a 30-minute meeting to walk through Winter Park / Maitland inventory, price ranges, and what pre-approval looks like when you're ready.<br><br>Want to lock that in this week or next?`",
     "`No pressure at all — luxury buyers often spend a year quietly looking before they engage an agent. Jeffrey and Renee are great people to talk to early because they don't push — it's a 30-minute meeting to walk through Windermere / Isleworth inventory, price ranges, and what pre-approval looks like when you're ready.<br><br>Want to lock that in this week or next?`"),
    ("Got it — Richard keeps Tuesday and Thursday afternoons open specifically for luxury buyers who need to move fast.",
     "Got it — the Funks keep Tuesday and Thursday afternoons open specifically for luxury buyers who need to move fast."),
    ("Solid timeline — Richard's planning meetings are perfect for that horizon.",
     "Solid timeline — the Funks' planning meetings are perfect for that horizon."),
    ("Smart to start early — gives Richard time to learn what you actually want, including off-market inventory that doesn't show up on search filters.",
     "Smart to start early — gives the Funks time to learn what you actually want, including off-market Windermere inventory that doesn't show up on search filters."),
    ("Selling luxury is its own discipline — most agents under-price luxury homes because they don't have comps for properties that rarely trade. Richard's brokerage focuses on luxury specifically. The two questions every luxury seller asks first: <em>\"What's the right number?\"</em> and <em>\"Who's the right buyer?\"</em><br><br>Both get answered properly in a 60-minute listing consultation at your home — Richard walks the property, pulls real luxury comps, and gives you a real strategy. Free, no obligation. What's your timeline?",
     "Selling luxury is its own discipline — most agents under-price Windermere homes because they don't have real comps for estates that rarely trade. The Funks focus on luxury specifically. The two questions every luxury seller asks first: <em>\"What's the right number?\"</em> and <em>\"Who's the right buyer?\"</em><br><br>Both get answered in a 60-minute listing consultation at your home — Jeffrey or Renee walks the property, pulls real luxury comps, and gives you a real strategy. Free, no obligation. What's your timeline?"),
    ("Understood — Richard can be at your door this week with comps and a positioning strategy.",
     "Understood — Jeffrey or Renee can be at your door this week with comps and a positioning strategy."),
    ("Perfect timeline — Richard can plan the staging, photography, and luxury-buyer positioning properly with that runway.",
     "Perfect timeline — the Funks can plan the staging, photography, and luxury-buyer positioning properly with that runway."),
    ("Smart to know your number before deciding — Richard will give you an honest luxury valuation, not a hype number.",
     "Smart to know your number before deciding — the Funks will give you an honest luxury valuation, not a hype number."),
    ("First-time luxury buyers face a different challenge than the typical first-timer — usually it's financing structure (jumbo, foreign income, asset-based) and understanding what differentiates luxury inventory from over-priced traditional homes. Richard walks first-time luxury buyers through this personally.",
     "First-time luxury buyers face a different challenge — usually it's financing structure (jumbo, foreign income, asset-based) and understanding what differentiates luxury inventory from over-priced traditional homes. The Funks walk first-time luxury buyers through this personally."),
    ("`Of course — type your question and I'll do my best. If it's something Richard needs to weigh in on personally (specific properties, offer strategy, neighborhood specifics), I'll route it to him and he'll get back to you in the morning.`",
     "`Of course — type your question and I'll do my best. If it's something Jeffrey or Renee needs to weigh in on personally (specific properties, offer strategy, Windermere neighborhood specifics), I'll route it to them and someone will get back to you in the morning.`"),
    ("Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Richard's calendar?",
     "Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on the Funks' calendar?"),
    ('<div class="booking-icon">P</div>', '<div class="booking-icon">F</div>'),
    ('<span class="value">Richard Palmano</span>', '<span class="value">Jeffrey or Renee Funk</span>'),
    ('<span class="value">150 N Orlando Ave, Winter Park</span>',
     '<span class="value">11550 Bridge House Rd, Windermere</span>'),
    ("(407) 232-5801", "(407) 438-4028"),
    ("Richard will text you a confirmation by 9 AM.",
     "Jeffrey or Renee will text you a confirmation by 9 AM."),
    ("Richard wants to pull comps before the visit.",
     "The Funks want to pull comps before the visit."),
    ("Richard will reach out", "The Funks will reach out"),
    ("Richard has been notified", "The Funks have been notified"),
    ("`No problem. Richard has openings", "`No problem. The Funks have openings"),
    ("palmanogroup.com", "realtyinorlando.com"),
]
FUNK_CLEANUP = [
    ("Richard Palmano", "Jeffrey & Renee Funk"),
    ("Richard", "the Funks"),
    ("Palmano Group", "The Funk Collection"),
    ("Palmano", "The Funk Collection"),
    ("Winter Park", "Windermere"),
]

# ---- LAKE NONA DENTAL GROUP — General dentistry (uses wayside.html) ----
NONADENTAL_SUBS = [
    ("Wayside Family Dental — After-Hours Concierge | Powered by Velo AI",
     "Lake Nona Dental Group — After-Hours Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Wayside Family Dental.",
     "This is a live demo built by Velo AI for Lake Nona Dental Group."),
    ("Sanford, Florida · Est. 2012", "Lake Nona, Florida · Family Dentistry"),
    ('<h1 class="practice-name">Wayside Family Dental</h1>',
     '<h1 class="practice-name">Lake Nona Dental Group</h1>'),
    ('<p class="practice-doctor">Dr. Lyudmila A. Onyski, DDS</p>',
     '<p class="practice-doctor">The Lake Nona Dental Team</p>'),
    ("Dr. Onyski is on call to respond to her patients' needs as soon as possible. As a patient of Wayside, you're never alone.",
     "The Lake Nona Dental Group team is committed to responding to patient needs as quickly as possible. As a patient of the practice, you're never alone."),
    ("4907 International Pkwy, Suite 1041<br>Sanford, FL 32771",
     "9145 Narcoossee Rd, Suite A100<br>Orlando, FL 32827"),
    ("<div>(407) 732-4570</div>", "<div>(407) 890-8003</div>"),
    ("<strong>Wayside Concierge</strong> · Available 24/7",
     "<strong>Lake Nona Dental Concierge</strong> · Available 24/7"),
    ("A patient of Wayside? Dr. Onyski will be notified immediately for urgent matters.",
     "A patient of Lake Nona Dental Group? The team will be notified immediately for urgent matters."),
    ("Good evening — you've reached the after-hours line for Wayside Family Dental. Dr. Onyski is unavailable right now, but I can help with most things and reach her directly if it's urgent.",
     "Good evening — you've reached the after-hours line for Lake Nona Dental Group. The team is wrapped for the day, but I can help with most things and reach the on-call doctor directly if it's urgent."),
    # Pronoun fix — switching to team
    ("Dr. Onyski has been doing both since 2010, so you're in capable hands.",
     "Lake Nona Dental Group has been performing both for years, so you're in capable hands."),
    ("Dr. Onyski has been welcoming new patients to Wayside since 2012",
     "Lake Nona Dental Group has been welcoming new patients to Lake Nona for years"),
    ("texting Dr. Onyski now — she'll call you back",
     "texting the on-call doctor now — they'll call you back"),
    ("Dr. Onyski will want to see you first thing — she keeps emergency slots",
     "The team will want to see you first thing — they keep emergency slots"),
    ("Lance has been notified", "The team has been notified"),
    ("Dr. Onyski's office", "the office"),
    ("Dr. Onyski has been notified", "The team has been notified"),
    ("Dr. Onyski opens new-patient slots", "The practice opens new-patient slots"),
    ("Dr. Onyski has openings", "The practice has openings"),
    ("Dr. Onyski needs to weigh in", "The doctor needs to weigh in"),
    ("she'll call", "they'll call"),
    ("she keeps emergency slots", "they keep emergency slots"),
    ("she calls", "they call"),
    ('<div class="booking-icon">W</div>', '<div class="booking-icon">L</div>'),
    ('<span class="value">Dr. Lyudmila A. Onyski</span>',
     '<span class="value">Lake Nona Dental Team</span>'),
    ('<span class="value">4907 International Pkwy, Suite 1041</span>',
     '<span class="value">9145 Narcoossee Rd, Orlando</span>'),
    ("(407) 732-4570", "(407) 890-8003"),
    ("Dr. Onyski", "the team"),
    ("Wayside", "Lake Nona Dental"),
]
NONADENTAL_CLEANUP = [
    ("Wayside", "Lake Nona Dental"),
    ("Onyski", "Lake Nona Dental"),
]


JOBS = [
    ("klausmanlaw", "ragland.html", KLAUSMAN_SUBS, KLAUSMAN_CLEANUP),
    ("frankfamilylaw", "ragland.html", FRANK_SUBS, FRANK_CLEANUP),
    ("sunbright", "homelis.html", SUNBRIGHT_SUBS, SUNBRIGHT_CLEANUP),
    ("goldie", "wayside.html", GOLDIE_SUBS, GOLDIE_CLEANUP),
    ("pigfloyds", "wayside.html", PIGFLOYDS_SUBS, PIGFLOYDS_CLEANUP),
    ("bacan", "pigfloyds.html", BACAN_SUBS, BACAN_CLEANUP),
    ("kadence", "pigfloyds.html", KADENCE_SUBS, KADENCE_CLEANUP),
    ("marcias", "goldie.html", MARCIAS_SUBS, MARCIAS_CLEANUP),
    ("velizkatz", "ragland.html", VELIZKATZ_SUBS, VELIZKATZ_CLEANUP),
    ("cullen", "klausmanlaw.html", CULLEN_SUBS, CULLEN_CLEANUP),
    ("palmano", "sunbright.html", PALMANO_SUBS, PALMANO_CLEANUP),
    # ---- BATCH 2 ----
    ("nami", "kadence.html", NAMI_SUBS, NAMI_CLEANUP),
    ("coro", "bacan.html", CORO_SUBS, CORO_CLEANUP),
    ("thelook", "goldie.html", THELOOK_SUBS, THELOOK_CLEANUP),
    ("lathamluna", "ragland.html", LATHAMLUNA_SUBS, LATHAMLUNA_CLEANUP),
    ("murphyberglund", "velizkatz.html", MURPHYBERGLUND_SUBS, MURPHYBERGLUND_CLEANUP),
    ("funkcollection", "palmano.html", FUNK_SUBS, FUNK_CLEANUP),
    ("lakenonadental", "wayside.html", NONADENTAL_SUBS, NONADENTAL_CLEANUP),
]


if __name__ == "__main__":
    for job in JOBS:
        slug, base, subs = job[0], job[1], job[2]
        cleanup = job[3] if len(job) > 3 else None
        print(f"\n=== {slug} (base: {base}) ===")
        build(slug, base, subs, cleanup)
