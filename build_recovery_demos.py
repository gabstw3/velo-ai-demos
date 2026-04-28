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


JOBS = [
    ("klausmanlaw", "ragland.html", KLAUSMAN_SUBS, KLAUSMAN_CLEANUP),
    ("frankfamilylaw", "ragland.html", FRANK_SUBS, FRANK_CLEANUP),
    ("sunbright", "homelis.html", SUNBRIGHT_SUBS, SUNBRIGHT_CLEANUP),
    ("goldie", "wayside.html", GOLDIE_SUBS, GOLDIE_CLEANUP),
    ("pigfloyds", "wayside.html", PIGFLOYDS_SUBS, PIGFLOYDS_CLEANUP),
]


if __name__ == "__main__":
    for job in JOBS:
        slug, base, subs = job[0], job[1], job[2]
        cleanup = job[3] if len(job) > 3 else None
        print(f"\n=== {slug} (base: {base}) ===")
        build(slug, base, subs, cleanup)
