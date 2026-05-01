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

# ============================================================================
# BATCH 2 v2 — DEEP customization with real prospect data
# (replaces the substitution-heavy v1 demos with research-backed unique ones)
# ============================================================================

# ---- NAMI v2 — Real data: Chefs Freddy Money + Jason Beliveau, 10-seat omakase counter
# at Lake Nona Wave Hotel, 18-bite tasting menu, $225pp, signature: lobster donuts with
# matcha, Nami Nuggets, tuna pizza, 67-seat dining room, Michelin-recognized
# ----
NAMI_V2_SUBS = [
    # Identity overrides (replace what was substituted in v1)
    ("Lake Nona, Orlando · Michelin-Recognized Omakase",
     "Lake Nona Wave Hotel · Michelin-Recognized"),
    ('<p class="practice-doctor">The Nami Team</p>',
     '<p class="practice-doctor">Chefs Freddy Money &amp; Jason Beliveau</p>'),
    ("Nami runs an intimate omakase service where the chefs can't pause for the phone — but reservation requests, waitlist inquiries, and dietary considerations get captured around the clock.",
     "Nami's 10-seat omakase counter is wrapped around the chef pass — Chefs Freddy and Jason can't step away mid-progression to take the phone. That's where reservation requests and dietary planning sit until morning, unless I catch them first."),
    ("Welcome to Nami. Service is intimate and the chefs can't pause to answer the phone — but I'm here to take reservation requests, manage the waitlist, walk through dietary considerations, and route anything special to the team.",
     "Welcome to Nami at Lake Nona Wave Hotel. The 67-seat dining room and the 10-seat omakase counter are mid-service — Chefs Freddy and Jason are at the pass and can't pick up. I'm here to take reservation requests, manage the waitlist, walk through dietary planning for the 18-bite tasting, and route anything special to the team."),
    ("Of course — Nami regularly has last-minute openings due to cancellations. I can add you to tonight's or this week's waitlist with priority based on flexibility. Tell me your party size and which night(s) work, and I'll text you the moment a seat opens up.",
     "Of course — both the omakase counter and the dining room have day-of cancellations regularly, especially weeknights. I can add you to tonight's or this week's waitlist with priority based on flexibility. Tell me your party size, which format you'd prefer (counter vs. dining room), and which nights work — I'll text the moment a seat opens up."),
    ("Buyouts at Nami are unique — the entire counter for your party, custom omakase progression. The chefs love planning these. What's the occasion?",
     "Buyouts at Nami are unique — Chef Freddy and Jason will craft a custom 18-bite progression for the occasion, with optional sake and wine pairings. Past buyouts have included engagement dinners, milestone birthdays, and corporate retreats from the Wave Hotel. What's the occasion?"),
    ("Of course — Nami is a multi-course omakase, so dietary accommodations need to be planned in advance. The team handles most allergens (shellfish, gluten, sesame) and can craft a fully vegan or pescatarian progression with 48hrs notice. What's the consideration?",
     "Of course — the 18-bite tasting weaves through European-influenced Japanese flavors (think the lobster donuts with matcha, the tuna pizza), so dietary planning matters. The team handles most allergens (shellfish, gluten, sesame, dairy) and can craft a fully vegan or pescatarian progression with 48 hours notice. What's the consideration?"),
    # Pricing reality
    ("Buyouts run $300-$500 per seat depending on the omakase progression and beverage pairing. The team does a planning call to understand occasion and dietary needs before quoting — that way the menu becomes part of the experience.",
     "The standard tasting is $225 per person with optional wine pairing at $155. Full counter buyouts are quoted on the planning call — the chefs want to understand occasion, dietary needs, and beverage program before pricing the experience."),
]
NAMI_V2_CLEANUP = []

# ---- CORO v2 — CORRECTION: NOT Spanish tapas. Chef-driven seasonal small plates.
# Open kitchen, "ever-evolving menu of bold seasonal dishes for sharing", 3022 Corrine Dr,
# phone is TEXT ONLY at 407-629-5005 (huge angle for AI concierge!), Tues-Thurs 5-9:30
# ----
CORO_V2_SUBS = [
    ("Coro — Reservations & Tapas Concierge | Powered by Velo AI",
     "Coro — Reservations Concierge | Powered by Velo AI"),
    ("Audubon Park, Orlando · Michelin Spanish Tapas",
     "Audubon Park, Orlando · Chef-Driven Seasonal Small Plates"),
    ('<p class="practice-doctor">The Coro Team</p>',
     '<p class="practice-doctor">The Coro Kitchen</p>'),
    ("Coro runs a refined Spanish tapas service where the team can't always pause to answer the phone — but reservations, dietary inquiries, and private events get captured around the clock.",
     "Coro is text-only at the host stand — that's a deliberate choice for an open-kitchen concept where the team is at the pass, not the phone. But text doesn't scale to dietary questions, large parties, or buyout inquiries. That's where I come in."),
    ("3201 Corrine Dr, Suite 100<br>Orlando, FL 32803",
     "3022 Corrine Drive<br>Orlando, FL 32803"),
    ("Welcome to Coro. The dining room is mid-service and the team can't always pick up — but I'm here. I can take reservations, scope private events, walk you through the tapas menu and dietary options, and route anything time-sensitive to the team.",
     "Welcome to Coro. The kitchen is open and the team is mid-service — by design, we don't take phone calls during service, just texts. That works for simple reservation confirmations but not for the bigger questions. I'm here to handle reservation requests, scope private events, walk through the seasonal menu and any dietary needs, and route anything time-sensitive to the team."),
    ("Private dining at Coro accommodates intimate dinners up to full restaurant buyouts. What kind of event are you considering?",
     "Coro does buyouts and large-party reservations, with the kitchen building a custom seasonal small-plates progression for your group. What's the event?"),
    ("Private dining at Coro starts at parties of 8 with a curated tapas progression, and scales to full restaurant buyouts. Pricing is typically $85-145 per person depending on the menu and beverage program. The team does a planning call before quoting so the menu actually fits the event.",
     "Buyouts and large-party menus at Coro start with a planning conversation — the kitchen wants to understand the occasion, the group's appetite for adventurous flavors, and any dietary considerations before designing the menu. Pricing typically lands $85-145 per person depending on the progression and beverage program."),
    ("Of course — type your question. Hours, the tapas menu, dietary stuff (the kitchen handles vegetarian and gluten-free with notice), or anything specific to a dish — I can usually answer right now.",
     "Of course — type your question. The menu rotates seasonally so I'll have current info on what's running. Dietary stuff (the kitchen handles vegetarian and gluten-free with reasonable notice), open-kitchen-specific questions, or anything about an event — I can usually answer right now."),
]
CORO_V2_CLEANUP = []

# ---- THE LOOK v2 — Real data: 17+ named stylists, REZO Certified (Solice), Hattori Hanzo
# trained, NovaLash certified, 90+ services across hair/spa/skincare, 4.9-star 1,100+
# reviews, brand partnerships (Wella, Brazilian Blowout, Moroccan Oil, Redken), 3635 Aloma
# Ave #1025 Oviedo, Mon 9-5/Tue-Thu 9-9/Wed-Fri 9-7/Sat 9-6
# ----
THELOOK_V2_SUBS = [
    ("Oviedo, Florida · Hair & Spa", "Oviedo, Florida · Hair, Spa &amp; Skincare"),
    ('<p class="practice-doctor">The Look Team</p>',
     '<p class="practice-doctor">17 Stylists · Award-Winning Team</p>'),
    ("The Look's full-service team handles hair, spa, and skincare under one roof — from the first booking inquiry at 11pm to the final treatment. The booking line never sleeps.",
     "Seventeen stylists, 90+ services, and 4.9 stars across 1,100+ Google reviews. The Look handles hair (Hattori Hanzo trained, REZO Certified for curls), spa, skincare, and lashes (NovaLash certified) under one roof. The booking line never sleeps."),
    ("151 Geneva Dr, Suite 1006<br>Oviedo, FL 32765",
     "3635 Aloma Ave, Suite 1025<br>Oviedo, FL 32765"),
    ("Tue–Sat · By Appointment", "Mon-Sat · See Hours"),
    ("Welcome to The Look. The salon and spa are wrapped for the night, but I'm here — I can quote services across hair, color, skincare, and spa, hold appointments, and answer most questions before you go to sleep.",
     "Welcome to The Look. The salon is wrapped for the night, but I can hold appointments across all 17 stylists, quote services (we do 90+, from precision Hattori Hanzo cuts to REZO Certified curl work to NovaLash extensions), and answer most questions before you go to sleep."),
    # The Look is a salon/spa hybrid — chip flow needs adjustment
    ("{ label: '💇 Cut or style', value: 'emergency' },\n        { label: '🎨 Color, balayage, or highlights', value: 'high-value' },\n        { label: '✨ Extensions or treatments', value: 'new-patient' },\n        { label: '❓ A pricing question', value: 'question' }",
     "{ label: '💇 Hair (cut/color/extensions)', value: 'emergency' },\n        { label: '✨ Lashes / brows / waxing', value: 'high-value' },\n        { label: '🌿 Spa / skincare / facials', value: 'new-patient' },\n        { label: '❓ A pricing question', value: 'question' }"),
    ("'emergency': 'I want a cut or style',\n      'high-value': \"I want color, balayage, or highlights\",\n      'new-patient': \"I want extensions or a treatment\"",
     "'emergency': 'I want a hair service (cut/color/extensions)',\n      'high-value': \"I want lashes, brows, or waxing\",\n      'new-patient': \"I want a spa or skincare service\""),
    # Smarter dialogue for hair branch (CURL specialty + REZO is unique)
    ("`Quick question so I know how to prioritize — when do you need it by?`,\n        1100,\n        [\n          { label: '🔴 This week — special event', value: 'severe' },\n          { label: '🟡 Within 2 weeks', value: 'moderate' },\n          { label: '🟢 Whenever there\\'s availability', value: 'mild' }\n        ]",
     "`Quick question so I match you with the right stylist — what kind of hair are you working with?`,\n        1100,\n        [\n          { label: '🌀 Curly / textured', value: 'severe' },\n          { label: '✨ Color / extensions', value: 'moderate' },\n          { label: '✂️ Cut / blowout', value: 'mild' }\n        ]"),
    # Severe → curl path (REZO specialist Solice)
    ("Got it — special event urgency. The team usually has a couple priority slots reserved each week for events. Let me get you on the calendar.<br><br>Can I get your first name and best phone number? Whatever the event is, we'll make sure you walk in feeling like the moment matters.",
     "Curls are a specialty — Solice Del Mazo is REZO Certified and books out fastest. The other curl-friendly stylists at The Look are also trained on the dry-cutting REZO method, so we can get you in either way.<br><br>Can I get your first name and best phone number? I'll have Solice or her team confirm in the morning."),
    ("Perfect timeline. Goldie's stylists keep mid-week slots open for new clients — Tuesday or Thursday work best.<br><br>What's your first name? I'll have someone pre-confirm with you by tomorrow morning.",
     "Color and extensions are core specialties at The Look — the salon partners with Wella, Brazilian Blowout, Moroccan Oil, and Redken, so most modern color work is in-house. Tuesday or Thursday have the most flexibility for new color clients.<br><br>What's your first name? I'll have someone pre-confirm with you by tomorrow morning."),
    # Color path → broader hair menu
    ("Smart move to reach out before you book — Goldie's colorists specialize in luxury color and would much rather hear what you're going for before you arrive than try to fix something rushed.<br><br>What kind of color are you thinking?",
     "Smart move to reach out before booking — most rushed lash and brow appointments end with regret. Tell me what you're after and I'll match you with the right specialist (the lash team is NovaLash certified, brows are done across multiple stylists, and waxing is full-service).<br><br>Which service are you thinking?"),
    # Cap services map for new chip flow
    ("'implants': 'balayage',\n      'invisalign': 'highlights',\n      'both': 'a color correction'",
     "'implants': 'classic lashes',\n      'invisalign': 'volume lashes',\n      'both': 'a brow service'"),
    ("Most clients asking about ${txt} have one of two questions: <em>\"Will it look natural on me?\"</em> and <em>\"What will it actually cost?\"</em><br><br>Both are best answered in a 15-minute consultation — your colorist looks at your hair, walks through what's realistic, and gives you a real quote before you commit to anything. Color appointments at Marcia's are typically 3-4 hours and run $250-$450 depending on length and complexity.<br><br>Want me to hold a consult slot this week?",
     "Most clients booking ${txt} are wondering: <em>\"Will it look natural?\"</em> and <em>\"How long does it last?\"</em><br><br>Both are best answered in a 15-minute consultation — the lash artist looks at your natural lashes, walks through what's realistic for your eye shape and lifestyle, and gives you a real quote and timing before you commit. Want me to hold a slot this week?"),
    # Extensions → spa / skincare
    ("Extensions are one of Goldie's specialties — the team is certified in hand-tied, tape-in, and luxury fusion methods. Most clients are deciding between three things: length, fullness, and how much maintenance they want to commit to.<br><br>The best way to figure out the right method is a 30-minute consultation where the team walks you through samples and color-matches in person. What's your first name?",
     "The Look's spa side handles facials (rejuvenating, anti-wrinkle), microblading, eyebrow tinting, full body waxing, and skincare consultations. The estheticians do continuing education quarterly so the techniques stay current. What's your first name? I'll have the right specialist follow up tomorrow morning."),
]
THELOOK_V2_CLEANUP = [("(321) 363-1233", "(407) 977-8481"), ("Goldie", "The Look")]

# ---- LATHAM LUNA v2 — World-Class Counsel / Small-Town Service tagline,
# 11 practice areas, Daniel = Bankruptcy Partner + Aviation Chair, est. 1996,
# Super Lawyers + Best Lawyers recognitions
# ----
LATHAMLUNA_V2_SUBS = [
    ("Orlando, Florida · Business Law", "Downtown Orlando · Est. 1996"),
    ("<h4>Business Law With Real Bandwidth</h4>",
     "<h4>World-Class Counsel · Small-Town Service</h4>"),
    ("Business matters rarely surface during business hours — vendor disputes hit Friday at 6pm, foreclosure deadlines fall on weekends, lien questions come in at midnight. Daniel is committed to being available when business actually moves.",
     "Latham Luna is a downtown Orlando boutique with eleven practice areas — bankruptcy, construction, commercial litigation, hospitality, aviation. The firm's positioning is &quot;World-Class Counsel, Small-Town Service.&quot; Daniel is committed to being available when business actually moves, not just when the office is open."),
    ("Good evening — you've reached the after-hours line for Latham Luna. Daniel handles business law, bankruptcy, and construction matters — vendor disputes, contract enforcement, foreclosure defense, mechanic's liens. He's wrapped for the day, but I can take down what's going on and get him back to you fast.",
     "Good evening — you've reached the after-hours line for Latham Luna in downtown Orlando. The firm covers eleven practice areas; Daniel chairs the Aviation Department and is a Bankruptcy Partner. He's wrapped for the day, but I can take down what's going on and route it to him or another attorney depending on the matter."),
    ("Daniel handles business law, bankruptcy, and construction matters every week",
     "Daniel and the Latham Luna team handle business, bankruptcy, and construction matters every week"),
    ("Business disputes are exactly what Daniel handles every week — non-payment, breach of contract, vendor disputes, partner disagreements. The two things that help him move fast: what's the dispute, and whether there's a deadline (court date, contract clause, payment deadline) anywhere in the next two weeks.",
     "Business disputes are core territory for Latham Luna — the firm's been doing this since 1996, with five attorneys in Florida Super Lawyers and six in Best Lawyers in America. Daniel handles bankruptcy specifically, and other partners cover commercial litigation, employment, and corporate matters. The two things that help the team move fast: what's the dispute, and whether there's a deadline anywhere in the next two weeks."),
    ("Construction matters move on tight statutory deadlines — mechanic's liens, notice to owner timing, payment bond claims. Daniel handles construction law specifically and the first thing he checks is whether you're inside the deadline window.",
     "Construction matters move on tight statutory deadlines — Florida lien notices, payment bond claims, contractor disputes. Latham Luna has a dedicated construction practice and the first thing the team checks is whether you're inside the statutory window."),
    ("Bankruptcy and foreclosure timing matters — there are filing windows, automatic stays, and hearing dates that can't slip. Daniel handles both consumer and small-business bankruptcy plus foreclosure defense. The first thing he wants to know is the urgency.",
     "Bankruptcy and foreclosure are Daniel's specialty — he's a Bankruptcy Partner at the firm. Filing windows, automatic stays, 341 meetings, and the difference between Chapter 7 vs Chapter 11 vs Chapter 13 are all conversations he has every week. The first thing he wants to know is your timeline urgency."),
]
LATHAMLUNA_V2_CLEANUP = []

# ---- MURPHY & BERGLUND v2 — Real data: VA-accredited, Cryptocurrency Law (Michelle's
# specialty — modern angle!), founded by Jodi + Michelle, 1101 Douglas Ave (xlsx wrong),
# (407) 865-9553 (xlsx wrong), 141 Birdeye reviews
# ----
MURPHYBERGLUND_V2_SUBS = [
    ("Altamonte Springs, Florida · Estate &amp; Elder Law",
     "Altamonte Springs, Florida · VA-Accredited · Estate &amp; Elder Law"),
    ("961 N Hunt Club Rd<br>Altamonte Springs, FL 32714",
     "1101 Douglas Ave<br>Altamonte Springs, FL 32714"),
    ("(407) 539-4040", "(407) 865-9553"),
    ("Estate planning, elder law, and family matters all surface during life's hardest transitions — declining health, the death of a parent, a Medicaid crisis. Michelle and Jodi are committed to being there during those moments. You're never alone.",
     "Estate planning, elder law, and family matters surface at life's hardest transitions — declining health, the death of a parent, a Medicaid eligibility crisis, a Veterans benefits question. Murphy &amp; Berglund is VA-accredited and handles both Medicaid planning and VA aid &amp; attendance. Jodi and Michelle are committed to being there during those moments."),
    ("Good evening — you've reached the after-hours line for Murphy & Berglund. The firm handles estate planning, elder law, family law, and probate. Both attorneys are wrapped for the day, but everything you share is confidential. I'll take down what's on your mind and get the right attorney to reach back out.",
     "Good evening — you've reached the after-hours line for Murphy & Berglund. The firm is VA-accredited and handles estate planning, probate, elder law, Medicaid &amp; VA planning, family law, and probate. Both attorneys are wrapped for the day, but everything you share is confidential. I'll route what's on your mind to whichever attorney fits — Jodi or Michelle — and have them reach back out."),
    ("I'm sorry — these calls are usually placed at one of the hardest moments. Jodi handles probate at the firm, including the post-loss paperwork most families don't know how to navigate. The two things that help her move quickly: who passed, and whether they had any documents in place.",
     "I'm sorry — these calls usually come at one of the hardest moments. Jodi handles probate and trust administration directly. She and Michelle have walked over a hundred families through the post-loss paperwork — the will or trust contest, asset retitling, creditor claims, the steps that nobody explains. The two things that help her move quickly: who passed, and whether they had documents in place."),
    ("Elder law calls usually surface around two specific events: a parent's care needs are escalating, or a Medicaid eligibility question just got real. Michelle handles elder law specifically — long-term care planning, asset protection, Medicaid qualification, guardianship.",
     "Elder law calls usually surface at one of three moments: parent's care needs escalating, a Medicaid eligibility question just got real, or a Veteran is being denied aid &amp; attendance benefits. Murphy &amp; Berglund is VA-accredited (rare for an estate firm) and handles all three — long-term care planning, Medicaid spend-down, asset protection trusts, VA benefits applications, guardianship."),
    ("Smart to think about this before you need it — most people put off estate planning until a crisis forces the conversation, which is exactly the wrong time. Jodi puts together wills, trusts, powers of attorney, and healthcare surrogates as a coordinated package.",
     "Smart to think about this before you need it. Michelle handles wills, trusts, powers of attorney, and healthcare surrogates as a coordinated package — and notably, she's one of the few estate attorneys in Central FL with a Cryptocurrency Law practice, which matters more every year as people hold digital assets without thinking about how they pass."),
    ("'estate': 'Probate Consultation',\n          'planning': 'Estate Planning Consultation',\n          'elder': 'Elder Law / Medicaid Consultation',\n          'question': 'General Consultation'",
     "'estate': 'Probate / Trust Admin Consultation',\n          'planning': 'Estate Planning + Crypto Asset Consult',\n          'elder': 'Elder Law / Medicaid / VA Benefits Consult',\n          'question': 'General Consultation'"),
]
MURPHYBERGLUND_V2_CLEANUP = []

# ---- FUNK COLLECTION v2 — 25+ years experience, 5x Real Trends Best Team,
# 8x ICON Agent, #2 internationally with eXp, 500+ 5-star reviews, Disney vacation
# homes niche, 130 agents under Jeff (luxury branch leader), 422 Main St Suite 1
# ----
FUNK_V2_SUBS = [
    ("Windermere, Florida · Luxury Estates",
     "Windermere, Florida · #2 Team Globally · eXp"),
    ("The luxury estate buyer doesn't browse Zillow at 9pm — they research specific properties on private golf communities and waterfront lots, and expect a considered conversation. The Funks' commitment is to respond with the kind of conversation Windermere luxury actually demands.",
     "Twenty-five years selling Windermere luxury, ranked #2 internationally with eXp Realty, 8x ICON Agent, 5x Real Trends Best Team. Buyers and sellers don't reach The Funk Collection casually — they reach out because they've done their research. Jeffrey and Renee are committed to responding with the kind of conversation that level of inquiry deserves."),
    ("11550 Bridge House Rd, Suite 200<br>Windermere, FL 34786",
     "422 Main Street, Suite 1<br>Windermere, FL 34786"),
    ("(407) 438-4028", "(407) 584-5463"),
    ("Welcome to The Funk Collection. I'm the after-hours concierge for Jeffrey and Renee — I can answer most questions, walk you through specific properties, and qualify what you're looking for. The Funks specialize in luxury estates in Windermere, Isleworth, and the gated communities around Lake Butler.",
     "Welcome to The Funk Collection. I'm the after-hours concierge for Jeffrey and Renee Funk. The team specializes in three Central Florida segments: luxury estates in Windermere/Isleworth/Dr Phillips, vacation homes near Walt Disney World, and investment properties throughout Orange and Lake counties. With 500+ 5-star reviews and Jeffrey leading eXp's downtown Windermere luxury branch (130 agents under him), the team's depth is the differentiator."),
    ("Great — the Funks' specialty is luxury estates in Windermere, Isleworth, and the surrounding gated communities. Inventory is thinner at this level and moves on different timing than the broader market, so the more I understand tonight, the more targeted they can be tomorrow.",
     "Great — the Funks specialize in three distinct buyer profiles: Windermere/Isleworth luxury, vacation/short-term-rental investment near Disney, and traditional residential. Each segment moves on completely different timing and inventory dynamics. The more I understand tonight, the more targeted Jeffrey or Renee can be tomorrow."),
    # Buyer financing path
    ("Perfect — the Funks work with several private lenders who specialize in luxury buyers and jumbo financing. They handle non-conforming loans, foreign buyers, and complex income situations that retail lenders fumble. Most luxury buyers save weeks doing it this way.",
     "Perfect — the Funks have a network of private lenders specifically for luxury, foreign-national, and investment-property buyers. Jumbo financing, asset-based lending, foreign buyer LLC structures, and DSCR loans for vacation rentals are all in-network. Most buyers at this level save weeks vs. retail banking."),
    ("`No pressure at all — luxury buyers often spend a year quietly looking before they engage an agent. Jeffrey and Renee are great people to talk to early because they don't push — it's a 30-minute meeting to walk through Windermere / Isleworth inventory, price ranges, and what pre-approval looks like when you're ready.<br><br>Want to lock that in this week or next?`",
     "`No pressure at all — luxury buyers often spend 12-18 months quietly looking before engaging an agent. Jeffrey and Renee are great early conversations because they don't push: it's a 30-minute meeting to walk through Windermere/Isleworth/Disney-area inventory, true price ranges (vs. Zillow estimates), and what financing looks like when you're ready.<br><br>Want to lock that in this week or next?`"),
    # First-time buyer luxury
    ("First-time luxury buyers face a different challenge — usually it's financing structure (jumbo, foreign income, asset-based) and understanding what differentiates luxury inventory from over-priced traditional homes. The Funks walk first-time luxury buyers through this personally.",
     "First-time luxury buyers face a different challenge than first-time traditional buyers. The financing structure is more complex (jumbo loans, asset-based lending, foreign income), and understanding what differentiates real luxury inventory from over-priced traditional listings is the harder skill. Jeffrey and Renee walk first-time luxury buyers through this directly — they've done it for 25+ years."),
    # Selling angle
    ("Selling luxury is its own discipline — most agents under-price Windermere homes because they don't have real comps for estates that rarely trade. The Funks focus on luxury specifically. The two questions every luxury seller asks first: <em>\"What's the right number?\"</em> and <em>\"Who's the right buyer?\"</em><br><br>Both get answered in a 60-minute listing consultation at your home — Jeffrey or Renee walks the property, pulls real luxury comps, and gives you a real strategy. Free, no obligation. What's your timeline?",
     "Selling Windermere luxury is its own discipline. Most agents under-price these homes because they don't have real comps — properties at this level rarely trade publicly, and the buyer pool is global. The Funks rank #2 globally at eXp specifically because they've built that buyer network. The two questions every luxury seller asks first: <em>\"What's the right number?\"</em> and <em>\"Who's the right buyer?\"</em><br><br>Both get answered in a 60-minute listing consultation at your home. What's your timeline?"),
]
FUNK_V2_CLEANUP = []

# ---- LAKE NONA DENTAL GROUP v2 — 6 dentists by name, 2 locations (Moss Park + Jack
# Brack), bilingual EN/ES, sedation dentistry + sleep apnea specialty, membership plan
# ----
NONADENTAL_V2_SUBS = [
    ("Lake Nona, Florida · Family Dentistry",
     "Lake Nona, Florida · Two Locations · Bilingual"),
    ('<p class="practice-doctor">The Lake Nona Dental Team</p>',
     '<p class="practice-doctor">Drs. Oslund · Yantorni · Montijo · Coughlin · Van · Van de Water</p>'),
    ("The Lake Nona Dental Group team is committed to responding to patient needs as quickly as possible. As a patient of the practice, you're never alone.",
     "Six dentists, two Lake Nona locations (Moss Park Rd and Jack Brack Rd), bilingual English/Spanish, sedation and sleep-apnea oral appliance specialties. The team is committed to responding to patient needs as quickly as possible — across both locations and after hours."),
    ("9145 Narcoossee Rd, Suite A100<br>Orlando, FL 32827",
     "Two Lake Nona Locations<br>Moss Park Rd · Jack Brack Rd"),
    ("(407) 890-8003", "(407) 277-1779"),
    ("Good evening — you've reached the after-hours line for Lake Nona Dental Group. The team is wrapped for the day, but I can help with most things and reach the on-call doctor directly if it's urgent.",
     "Good evening — you've reached the after-hours line for Lake Nona Dental Group. We have two Lake Nona locations and six dentists, plus Spanish-speaking staff. The on-call doctor rotates nightly. I can help with most things — and if it's urgent, I can reach whoever's on call directly."),
    ("Lake Nona Dental Group has been performing both for years, so you're in capable hands.",
     "Lake Nona Dental Group has handled both since the practice opened. Dr. Yantorni (FICOI — that's the implant credential) leads implant work, and the team includes orthodontic Invisalign providers. Either way, you're in capable hands."),
    ("Lake Nona Dental Group has been welcoming new patients to Lake Nona for years",
     "Lake Nona Dental Group has been welcoming new patients across both Moss Park Rd and Jack Brack Rd locations for years"),
    ("texting the on-call doctor now — they'll call you back",
     "texting the on-call doctor (rotation between the six DDS/DMDs on staff) now — they'll call you back"),
    ("'implants': 'Dental Implant Consultation',\n          'invisalign': 'Invisalign Consultation',\n          'both': 'Implant & Invisalign Consultation',\n          'emergency': 'Emergency Visit'",
     "'implants': 'Dental Implant Consultation (Dr. Yantorni)',\n          'invisalign': 'Invisalign Consultation',\n          'both': 'Implant & Invisalign Consultation',\n          'emergency': 'Emergency Visit (sedation available)'"),
    # Sedation specialty mention
    ("Of course — go ahead and type your question and I'll do my best. If it's something the doctor needs to weigh in on personally, I'll route it to her and she'll get back to you in the morning.",
     "Of course — type your question. We have specifics on sedation dentistry, sleep apnea oral appliances, our membership plan for uninsured patients, and which insurances we're in-network with. If it's something a doctor needs to weigh in on personally, I'll route it for morning follow-up."),
]
NONADENTAL_V2_CLEANUP = []

# ============================================================================
# ROUND 3 — Deep-research demos for 7 more xlsx prospects
# ============================================================================

# ---- CONAN & HERMAN — Criminal Defense, Orlando (base: klausmanlaw.html) ----
# Real data: Mark Conan (Avvo 9.8) + J. Scott Herman, 70+ yrs combined,
# 24/7 actual-attorney availability, practice: DUI/drugs/theft/DV/assault/burglary/VOP
CONAN_SUBS = [
    ("Klausman Law — After-Hours Intake | Powered by Velo AI",
     "Conan &amp; Herman — Criminal Defense Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Klausman Law",
     "This is a live demo built by Velo AI for The Law Office of Conan &amp; Herman"),
    ("Winter Park, Florida · Est. 1998",
     "Orlando, Florida · 70+ Years Combined · Criminal Defense"),
    ('<h1 class="practice-name">Klausman Law</h1>',
     '<h1 class="practice-name">Conan &amp; Herman</h1>'),
    ('<p class="practice-doctor">Glenn Klausman, Esq.</p>',
     '<p class="practice-doctor">Mark Conan &amp; J. Scott Herman, Esq.</p>'),
    ("Accidents and insurance disputes don't wait for business hours. Glenn is committed to being the first call you can actually reach — and the last call you'll need to make.",
     "Arrests don't wait for business hours. Conan &amp; Herman is the rare firm where an actual attorney answers — not a service. They've already built that around-the-clock availability. The intake assistant just makes sure no detail gets lost in the first ten minutes."),
    ("1101 N Lakemont Ave, Suite 200<br>Winter Park, FL 32792",
     "Orlando, FL · Lake County · Central Florida"),
    ("(407) 917-1718", "(407) 872-3999"),
    ("Mon–Fri 9a–5p · Free Consultation",
     "24/7 Attorney Available · Free Consultation"),
    ("<strong>Klausman Intake</strong> · Available 24/7",
     "<strong>Conan &amp; Herman Intake</strong> · 24/7 Attorney Reachable"),
    ("Already a client? Glenn will be notified directly for urgent matters on your case.",
     "Already a client? Mark or Scott will be notified directly for urgent matters on your case."),
    ("Good evening — you've reached the after-hours line for Klausman Law. Glenn handles personal injury and insurance disputes — accident cases, denied claims, and workers' comp. He's not available right this minute, but I can take down what happened and get him on a call with you fast.",
     "Good evening — you've reached the after-hours line for Conan &amp; Herman. Mark and Scott handle criminal defense exclusively — DUI, drug crimes, theft, domestic violence, assault, burglary, violations of probation, DMV hearings. The firm is one of the few in Central FL where an actual attorney answers 24/7 (not a service). One of them will be on with you within minutes — I'm here to capture the basics so they're already up to speed when they call."),
    # Chips — criminal defense specific
    ("{ label: '🚑 Recent accident or injury', value: 'accident' },\n        { label: '⚖️ Insurance denied my claim', value: 'insurance' },\n        { label: '💼 Workers\\' comp question', value: 'comp' },\n        { label: '❓ A general question', value: 'question' }",
     "{ label: '🚨 Just arrested / in custody', value: 'accident' },\n        { label: '🚗 DUI / drug charges', value: 'insurance' },\n        { label: '⚖️ Violation of probation', value: 'comp' },\n        { label: '❓ A general question', value: 'question' }"),
    ("'accident': \"I was recently in an accident or got injured\",\n      'insurance': \"My insurance company denied my claim\",\n      'comp': \"I have a workers' comp question\"",
     "'accident': \"Someone was just arrested or is in custody\",\n      'insurance': \"DUI or drug charges\",\n      'comp': \"Violation of probation\""),
    # Custody/arrest path
    ("I'm sorry you're dealing with this — accidents leave you with pain, paperwork, and pressure all at once. Glenn has handled thousands of injury cases in 27 years and the first thing he usually does is take that pressure off you so you can focus on healing. Two things help him move fast when he calls back: when did the accident happen, and have you talked to any insurance adjusters yet.",
     "Take a breath. The first hours after an arrest matter — what gets said to police, what doesn't, whether bond gets posted quickly. Conan &amp; Herman has 70+ years of combined criminal defense experience, and one of the things they're known for is getting incarcerated clients released within hours of intake. Two things that help them move immediately: who's in custody, and what jail or facility."),
    ("`First — when did the accident happen?`,\n        900,\n        [\n          { label: 'Today / yesterday', value: 'today' },\n          { label: 'Within the last week', value: 'week' },\n          { label: 'A while ago', value: 'older' }\n        ]",
     "`First — what's the relationship?`,\n        900,\n        [\n          { label: 'It\\'s me', value: 'today' },\n          { label: 'Family member', value: 'week' },\n          { label: 'Friend / other', value: 'older' }\n        ]"),
    ("'today': \"Today or yesterday\",\n      'week': \"Within the last week\",\n      'older': \"It's been a while\"",
     "'today': \"It's me\",\n      'week': \"Family member\",\n      'older': \"Friend or someone else\""),
    ("if (['today', 'week', 'older'].includes(value)) {\n      memory.timing = value;\n      await addBotMessage(\n        `Got it. Have you spoken with the at-fault driver's insurance company yet?`,\n        900,\n        [\n          { label: 'No, not yet', value: 'no-insurance' },\n          { label: 'Yes — they called me', value: 'yes-insurance' },\n          { label: 'They denied me', value: 'denied-insurance' }\n        ]\n      );\n      return;\n    }",
     "if (['today', 'week', 'older'].includes(value)) {\n      memory.relation = value;\n      await addBotMessage(\n        `Got it. Has anyone spoken to police or made a statement yet?`,\n        900,\n        [\n          { label: 'No statement made', value: 'no-insurance' },\n          { label: 'Brief one already', value: 'yes-insurance' },\n          { label: \"I'm not sure\", value: 'denied-insurance' }\n        ]\n      );\n      return;\n    }"),
    ("['no-insurance', 'yes-insurance', 'denied-insurance'].includes(value)",
     "['no-insurance', 'yes-insurance', 'denied-insurance'].includes(value)"),
    ("memory.insuranceContact = value;\n      await addBotMessage(\n        `Got it. One more question, then I'll get this in front of Glenn — are you currently in pain or did you have to go to the ER? That changes how fast he wants to get back to you.`,",
     "memory.statement = value;\n      await addBotMessage(\n        `Got it. One more — is bond an immediate issue, or is the focus more on the case itself right now?`,"),
    ("'urgent-frozen': \"Yes — ER visit / ongoing pain\",\n      'urgent-soon': \"Some pain but managing\",\n      'urgent-planning': \"No injuries, just need legal help\"",
     "'urgent-frozen': \"Bond is critical right now\",\n      'urgent-soon': \"Bond posted, focused on the case\",\n      'urgent-planning': \"No bond issue\""),
    ("[\n          { label: '🔴 Yes — ER visit or ongoing pain', value: 'urgent-frozen' },\n          { label: '🟡 Some pain but managing', value: 'urgent-soon' },\n          { label: '🟢 Not injured, just need legal help', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Bond is critical', value: 'urgent-frozen' },\n          { label: '🟡 Bond posted, case-focused', value: 'urgent-soon' },\n          { label: '🟢 No bond issue', value: 'urgent-planning' }\n        ]"),
    ("`Understood — Glenn wants to hear from you ASAP if you're hurt. I'm flagging this as priority and he'll call you within the hour during business hours, or first thing in the morning if it's late tonight.<br><br>Can I get your first name and best callback number? If you're at a hospital, please mention it.`",
     "`Understood — bond and the first 24 hours are exactly when Conan &amp; Herman move fastest. They've gotten clients released within hours of an intake call. I'm flagging this as priority — Mark or Scott will call you within minutes (24/7 attorney availability is one of the firm's actual differentiators).<br><br>Can I get your first name, the best callback number, and the jail or facility name?`"),
    ("`Thank you — that helps. Glenn offers free consultations for injury cases — no fee unless he wins your case. He'll review the situation, walk you through what your case might be worth, and explain the timeline so you know what to expect.<br><br>What's your first name? I'll have him reach out tomorrow to set up the call.`",
     "`Thank you — that helps. Conan &amp; Herman offers free consultations for criminal cases. Mark or Scott will review the charges, walk you through realistic outcomes (dismissal, plea, trial), and explain the timeline before you commit to anything.<br><br>What's your first name? I'll have one of them reach out as soon as possible — usually within the hour, even at this time.`"),
    # DUI/drug path
    ("if (value === 'insurance') {\n      memory.matter = 'insurance';\n      await addBotMessage(\n        `Insurance denials are exactly what Glenn handles every week. Insurance companies count on people accepting the first 'no' — they're often wrong, and a properly contested claim can flip outcome and dollar amount dramatically.<br><br>Most clients in your shoes are wondering: <em>\"Was the denial legitimate?\"</em> and <em>\"Is fighting it worth it?\"</em><br><br>Both are answered in a free consultation — Glenn reviews your denial letter and policy, tells you straight whether you have a case, and only takes it if he thinks you'll win. Want me to hold a slot this week?`,",
     "if (value === 'insurance') {\n      memory.matter = 'dui-drug';\n      await addBotMessage(\n        `DUI and drug charges are core territory for Conan &amp; Herman — they handle these weekly. The first questions every client has: <em>\"Will I lose my license?\"</em> and <em>\"Can this charge be reduced or dismissed?\"</em><br><br>Both are answered in a free consultation. Mark or Scott will review the arrest report, check whether the stop and search were lawful, and tell you straight what's defensible and what isn't. Want me to hold a slot — they have same-day availability for new criminal matters.`,"),
    # VOP path
    ("if (value === 'comp') {\n      memory.matter = 'comp';\n      await addBotMessage(\n        `Workers' comp can feel impossible to navigate — most claimants are dealing with HR pressure, doctors who work for the employer, and a system designed to deny first and pay last. Glenn has handled hundreds of these cases.<br><br>Just so I get the right urgency to him: are you currently off work, having benefits denied, or planning ahead?`,",
     "if (value === 'comp') {\n      memory.matter = 'vop';\n      await addBotMessage(\n        `Violations of probation move fast — there's usually a hearing date and the difference between getting prepared and showing up unprepared can mean the difference between continuing probation vs. doing the underlying sentence. Mark and Scott handle VOP hearings regularly.<br><br>Where are you on the timeline — is there a hearing already scheduled?`,"),
    ("[\n          { label: '🔴 Off work / benefits denied', value: 'urgent-frozen' },\n          { label: '🟡 Working but in pain', value: 'urgent-soon' },\n          { label: '🟢 Just need legal advice', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Hearing in the next 7 days', value: 'urgent-frozen' },\n          { label: '🟡 Hearing within 30 days', value: 'urgent-soon' },\n          { label: '🟢 Just received notice', value: 'urgent-planning' }\n        ]"),
    ("Of course — type your question. If it's something Glenn needs to weigh in on personally (case strategy, settlement evaluation, opposing counsel), I'll route it to him and he'll get back to you in the morning.",
     "Of course — type your question. If it's something Mark or Scott needs to weigh in on personally (case strategy, plea evaluation, hearing prep), I'll route it and one of them will get back to you (often within an hour given their 24/7 attorney availability)."),
    ('<div class="booking-icon">K</div>', '<div class="booking-icon">C</div>'),
    ('<span class="value">Glenn Klausman, Esq.</span>',
     '<span class="value">Mark Conan or J. Scott Herman, Esq.</span>'),
    ('<span class="value">1101 N Lakemont Ave, Winter Park</span>',
     '<span class="value">Orlando · Lake County</span>'),
    ("'insurance': 'Insurance Dispute Consultation (Free)',\n          'comp': 'Workers Comp Consultation (Free)',\n          'accident': 'Accident Case Consultation (Free)',\n          'question': 'General Consultation (Free)'",
     "'dui-drug': 'DUI / Drug Charge Consult (Free)',\n          'vop': 'Violation of Probation Consult (Free)',\n          'accident': 'Arrest / Custody Intake (Free)',\n          'question': 'General Consultation (Free)'"),
    ("(407) 917-1718", "(407) 872-3999"),
    ("Glenn", "Mark or Scott"),  # final cleanup
]
CONAN_CLEANUP = [
    ("Klausman", "Conan & Herman"),
    ("Glenn", "Mark or Scott"),
]

# ---- THE BOUTTY LAW FIRM — Sanford (base: ragland.html) ----
# Benjamin Shane Boutty: 20+ yrs construction industry + Florida Certified Contractor +
# UF MBA + UF JD cum laude 2010 + FL Bar 2011. Practice: estate, real estate, construction
BOUTTY_SUBS = [
    ("Lance A. Ragland, P.A. — After-Hours Intake | Powered by Velo AI",
     "The Boutty Law Firm — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Lance A. Ragland, P.A.",
     "This is a live demo built by Velo AI for The Boutty Law Firm"),
    ("Winter Springs, Florida · Est. 2015",
     "Sanford, Florida · Construction · Estate · Real Estate"),
    ('<h1 class="practice-name">Lance A. Ragland, P.A.</h1>',
     '<h1 class="practice-name">The Boutty Law Firm</h1>'),
    ('<p class="practice-doctor">Lance A. Ragland, Esq.</p>',
     '<p class="practice-doctor">Benjamin Shane Boutty, Esq. &amp; Florida Certified Contractor</p>'),
    ("<h4>Available When You Need Him</h4>",
     "<h4>The Rare Lawyer-Contractor Combination</h4>"),
    ("Estate matters rarely surface during business hours. Lance is committed to being there for clients during life's most difficult transitions. You're never alone.",
     "Construction disputes, estate matters, and real-estate closings all surface outside business hours. What's rare about The Boutty Law Firm: Shane spent 20+ years as a contractor before law school. When he reads a construction contract, he reads it the way the construction industry actually operates — not just the way lawyers parse contracts."),
    ("5750 Canton Cove<br>Winter Springs, FL 32708",
     "616 W 1st Street<br>Sanford, FL 32771"),
    ("(407) 960-6069", "(407) 622-1395"),
    ("By Appointment · Mon–Fri 9a–5p", "Mon–Fri 9a–5p · Sanford"),
    ("<strong>Ragland Intake</strong> · Available 24/7",
     "<strong>Boutty Law Intake</strong> · Available 24/7"),
    ("A current client of Lance's? He'll be notified directly for urgent matters.",
     "A current client of the firm? Shane will be notified directly for urgent matters."),
    ("Good evening — you've reached the after-hours line for the Law Offices of Lance A. Ragland. Lance focuses entirely on estate planning, probate, and trust matters. He's unavailable right now, but I can take down what's on your mind and get him to reach back out.",
     "Good evening — you've reached the after-hours line for The Boutty Law Firm in Sanford. Shane handles construction law, estate planning, probate, and real estate. What's distinctive about the firm: Shane is both a Florida-licensed attorney and a Florida Certified Contractor with 20+ years in the construction industry. He's wrapped for the day, but I can take down what's on your mind."),
    ("{ label: '🕯️ I lost a loved one', value: 'probate' },\n        { label: '📜 Plan a will or trust', value: 'planning' },\n        { label: '🏥 Power of attorney / healthcare', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }",
     "{ label: '🏗️ Construction dispute or defect', value: 'probate' },\n        { label: '🕯️ Estate / probate / will or trust', value: 'planning' },\n        { label: '🏠 Real estate transaction', value: 'poa' },\n        { label: '❓ A general question', value: 'question' }"),
    ("'probate': \"I lost a loved one and need probate help\",\n      'planning': \"I'd like to plan a will or trust\",\n      'poa': \"I need a power of attorney or healthcare paperwork\"",
     "'probate': \"I have a construction matter\",\n      'planning': \"I have an estate / probate / planning matter\",\n      'poa': \"I have a real estate transaction\""),
    # Construction path (was probate path)
    ("if (value === 'probate') {\n      memory.matter = 'probate';\n      await addBotMessage(\n        `I'm so sorry for your loss. Please take whatever time you need.<br><br>Lance has guided families through probate for nearly thirty years, and most of what feels overwhelming right now has a clear path forward. The two things that help him move quickly when he calls you back: who passed, and whether they had a will.`,",
     "if (value === 'probate') {\n      memory.matter = 'construction';\n      await addBotMessage(\n        `Construction matters are core territory for Shane — he's a Florida Certified Contractor in addition to being an attorney, so he understands both the legal framework and how construction actually operates. The two things that help him move fast: what kind of dispute, and whether there's a deadline (lien notice window, bond claim deadline, court date) anywhere soon.`,"),
    ("`If you're able to share — who is this for?`,\n        900,\n        [\n          { label: 'Spouse', value: 'spouse' },\n          { label: 'Parent', value: 'parent' },\n          { label: 'Other family member', value: 'other-family' }\n        ]",
     "`If you're able to share — what kind of construction matter?`,\n        900,\n        [\n          { label: 'Defect / workmanship', value: 'spouse' },\n          { label: 'Payment / lien dispute', value: 'parent' },\n          { label: 'Contract review / drafting', value: 'other-family' }\n        ]"),
    ("'spouse': \"My spouse\",\n      'parent': \"A parent\",\n      'other-family': \"Another family member\"",
     "'spouse': \"Construction defect or workmanship issue\",\n      'parent': \"Payment or lien dispute\",\n      'other-family': \"Contract review or drafting\""),
    ("if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.relation = value;\n      await addBotMessage(\n        `Thank you. Did they have a will or any estate documents in place?`,\n        900,\n        [\n          { label: 'Yes, they had a will', value: 'has-will' },\n          { label: 'No', value: 'no-will' },\n          { label: \"I'm not sure\", value: 'unsure-will' }\n        ]\n      );\n      return;\n    }",
     "if (['spouse', 'parent', 'other-family'].includes(value)) {\n      memory.constructionType = value;\n      await addBotMessage(\n        `Thank you. Are you the property owner, the contractor, or somewhere else in the chain?`,\n        900,\n        [\n          { label: 'Property owner', value: 'has-will' },\n          { label: 'Contractor / sub', value: 'no-will' },\n          { label: 'Lender / other', value: 'unsure-will' }\n        ]\n      );\n      return;\n    }"),
    ("memory.hasWill = value;\n      await addBotMessage(\n        `Got it. One more question, then I'll get this in front of Lance — is anything time-pressured? Sometimes accounts get frozen, or a property has a deadline. Other times there's just no rush.`,",
     "memory.party = value;\n      await addBotMessage(\n        `Got it. One more — Florida construction has tight statutory deadlines (notice to owner, lien filing windows, bond claim periods). Are you inside one of those windows right now?`,"),
    ("'urgent-frozen': \"Yes — accounts are frozen / property at risk\",\n      'urgent-soon': \"Soon, but not in crisis\",\n      'urgent-planning': \"No urgency — just planning ahead\"",
     "'urgent-frozen': \"Yes — deadline within 7 days\",\n      'urgent-soon': \"Within 30 days\",\n      'urgent-planning': \"No deadline\""),
    ("[\n          { label: '🔴 Yes — accounts frozen / property at risk', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not in crisis', value: 'urgent-soon' },\n          { label: '🟢 No urgency — just planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Deadline within 7 days', value: 'urgent-frozen' },\n          { label: '🟡 Within 30 days', value: 'urgent-soon' },\n          { label: '🟢 No deadline', value: 'urgent-planning' }\n        ]"),
    ("`Understood — that's exactly the kind of thing Lance wants to know about right away. I'm flagging this as priority and Lance will call you first thing tomorrow morning, before his appointments start.<br><br>Can I get your first name and best callback number? If a deadline is in the next 48 hours, please mention it.`",
     "`Understood — Florida construction deadlines are unforgiving. Shane wants to know immediately when there's a window in play. I'm flagging this as priority and he'll call first thing tomorrow before appointments start.<br><br>Can I get your first name and best callback number? If a deadline is in the next 48 hours, please mention it.`"),
    ("`Thank you — that helps. Lance opens his calendar Tuesday through Thursday for new probate matters and sets aside ninety minutes per consultation so nothing feels rushed.<br><br>What's your first name? I'll have him reach out by mid-morning to set a time that works.`",
     "`Thank you — that helps. Shane keeps consultation slots Tuesday through Thursday for new construction matters. The consult is where he tells you straight whether you're in a winnable position based on both the legal framework and what the construction industry will actually show in evidence.<br><br>What's your first name? I'll have him reach out tomorrow morning.`"),
    # Estate path
    ("if (value === 'planning') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart of you to think about this — most people put off estate planning for years and regret the procrastination. Lance has been doing wills, trusts, and estate plans exclusively since 2015, so this is exactly his bread and butter.<br><br>Most clients in your shoes are weighing one of two things: <em>\"Do I just need a will, or do I need a trust?\"</em> and <em>\"What's this going to cost me?\"</em><br><br>Both are answered properly in a one-hour consult — Lance reviews your situation, walks you through the difference, and gives you a flat-fee quote before you commit to anything. Want me to hold a slot this week or next?`,",
     "if (value === 'planning') {\n      memory.matter = 'estate';\n      await addBotMessage(\n        `Estate matters at The Boutty Law Firm cover the full range — wills, trusts, probate administration, and probate / trust litigation when families end up in dispute. Shane handles all of these.<br><br>Most clients are weighing one of two things: <em>\"What's the right structure?\"</em> and <em>\"What will this actually cost?\"</em><br><br>Both are answered in a 60-minute consult. Want me to hold a slot this week or next?`,"),
    # Real estate path (was POA)
    ("if (value === 'poa') {\n      memory.matter = 'poa';\n      await addBotMessage(\n        `These conversations are hard — usually they come up because someone in the family is going through a health change. Lance can put together a power of attorney and healthcare surrogate quickly, often within a few days if needed.<br><br>Just so I get the right urgency to him: is this for an immediate situation, or planning ahead?`,",
     "if (value === 'poa') {\n      memory.matter = 'realestate';\n      await addBotMessage(\n        `Real estate transactions at The Boutty Law Firm range from residential closings to commercial deals to complex transactions involving construction issues (which is where Shane's contractor background really shows up).<br><br>Just so I route this right: is this a transaction in progress, a dispute, or planning ahead?`,"),
    ("[\n          { label: '🔴 Immediate — health is declining', value: 'urgent-frozen' },\n          { label: '🟡 Soon, but not crisis', value: 'urgent-soon' },\n          { label: '🟢 Planning ahead', value: 'urgent-planning' }\n        ]",
     "[\n          { label: '🔴 Closing this week / dispute active', value: 'urgent-frozen' },\n          { label: '🟡 Within the month', value: 'urgent-soon' },\n          { label: '🟢 Planning ahead', value: 'urgent-planning' }\n        ]"),
    ("`Of course — go ahead and type your question. If it's something Lance needs to weigh in on personally, I'll route it to him and he'll get back to you in the morning. If it's something I can answer from his practice info, I'll do my best.`",
     "`Of course — type your question. If it's about construction (where Shane's lawyer-and-contractor background matters), estate planning, or real estate, I'll route it to him and he'll get back to you in the morning.`"),
    ('<div class="booking-icon">L</div>', '<div class="booking-icon">B</div>'),
    ('<span class="value">Lance A. Ragland, Esq.</span>',
     '<span class="value">Benjamin Shane Boutty, Esq.</span>'),
    ('<span class="value">5750 Canton Cove, Winter Springs</span>',
     '<span class="value">616 W 1st Street, Sanford</span>'),
    ("'planning': 'Estate Planning Consultation',\n          'poa': 'Power of Attorney Consultation',\n          'probate': 'Probate Consultation',\n          'question': 'General Consultation'",
     "'estate': 'Estate / Trust / Probate Consult',\n          'realestate': 'Real Estate Consult',\n          'construction': 'Construction Law Consult',\n          'question': 'General Consultation'"),
    ("(407) 960-6069", "(407) 622-1395"),
    ("Lance", "Shane"),
]
BOUTTY_CLEANUP = [
    ("Lance", "Shane"),
    ("Ragland", "Boutty"),
]

# ---- OLYMPUS EXECUTIVE REALTY — 100% commission, top producer brokerage ----
# Different angle: NOT a buyer/seller pitch — this is for AGENT recruitment + their
# top producers' lead handling. Base: palmano.html
OLYMPUS_SUBS = [
    ("Palmano Group — Luxury RE Concierge | Powered by Velo AI",
     "Olympus Executive Realty — Top-Producer Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Palmano Group.",
     "This is a live demo built by Velo AI for Olympus Executive Realty."),
    ("Winter Park, Florida · Boutique Luxury",
     "Montverde · Florida's Premier 100% Commission Brokerage"),
    ('<h1 class="practice-name">Palmano Group</h1>',
     '<h1 class="practice-name">Olympus Executive Realty</h1>'),
    ('<p class="practice-doctor">Richard Palmano, Broker</p>',
     '<p class="practice-doctor">Home of Top Producers · 100% Commission</p>'),
    ("<h4>Concierge for Luxury Buyers and Sellers</h4>",
     "<h4>Top Producer Lead Handling, 24/7</h4>"),
    ("The luxury estate buyer doesn't browse Zillow at 9pm — they research specific properties on private golf communities and waterfront lots, and expect a considered conversation. Richard's commitment is to be the broker who actually responds with the kind of conversation Windermere luxury actually demands.",
     "Olympus is built around top producers who keep 100% of their commissions. That model works because the leads they generate are theirs to handle directly — but top producers are also the ones with the least bandwidth to answer 9pm phone calls. The Olympus concierge captures and qualifies after-hours leads at the brokerage level, then routes to the right producer based on geography and specialty."),
    ("150 N Orlando Ave, Suite 200<br>Winter Park, FL 32789",
     "16903 Lakeside Drive, Suite 6<br>Montverde, FL 34756"),
    ("(407) 232-5801", "(407) 469-2000"),
    ("<strong>Palmano Concierge</strong> · Available 24/7",
     "<strong>Olympus Concierge</strong> · 24/7 Lead Capture"),
    ("Already working with Richard? He'll be notified directly for active deals.",
     "Already working with an Olympus producer? They'll be notified directly for active deals."),
    ("Welcome to Palmano Group. I'm Richard's after-hours concierge — I can answer most questions, walk you through specific properties, and qualify what you're looking for. Palmano specializes in luxury homes throughout Winter Park, Maitland, and the Orlando luxury corridor.",
     "Welcome to Olympus Executive Realty. We're a top-producer brokerage with offices in Orlando, Tampa, Clermont, and Montverde — over 100 agents covering everything from luxury Lake County estates to Tampa Bay condos to Orlando vacation homes. I'm here to qualify what you're looking for and route you to the producer best suited for your area and price range."),
    ("Great — Richard's specialty is the luxury market in Winter Park and the Orlando luxury corridor. The luxury inventory is thinner and moves on different timing than the broader market, so the more I understand about what you're looking for tonight, the more targeted Richard can be tomorrow.",
     "Great — Olympus has producers across Lake County, Orange County, Hillsborough, and Pinellas. Each producer specializes in different markets and price points. The more I understand tonight, the better I can match you with the right one — luxury vs. investor vs. first-time-buyer all live with different specialists at the brokerage."),
    ("Perfect — Richard works with several private lenders who specialize in luxury buyers and jumbo financing. They handle non-conforming loans, foreign buyers, and complex income situations that retail lenders fumble. Most luxury buyers save weeks doing it this way.",
     "Perfect — Olympus has preferred-lender relationships across the buyer spectrum: jumbo and luxury lenders, FHA and conventional specialists, foreign-buyer LLC structures, and DSCR loans for investors. Whichever producer matches your situation will introduce you to the right lender directly."),
    ("`No pressure at all — luxury buyers often spend a year quietly looking before they engage an agent. Richard's a great person to talk to early because he doesn't push — he's a 30-minute meeting to walk through Winter Park / Maitland inventory, price ranges, and what pre-approval looks like when you're ready.<br><br>Want to lock that in this week or next?`",
     "`No pressure at all — most Olympus producers prefer talking to early-stage buyers because that's when the relationship gets built right. Once I know roughly which market and price range, I can match you with a producer who'll do a 30-minute zero-pressure mapping call: neighborhoods, ranges, what pre-approval looks like.<br><br>Want to lock that in this week or next?`"),
    ("Got it — Richard keeps Tuesday and Thursday afternoons open specifically for luxury buyers who need to move fast.",
     "Got it — fast-moving buyers route to producers who keep specific availability for active buyers. Tuesday and Thursday afternoons are common slots."),
    ("Solid timeline — Richard's planning meetings are perfect for that horizon.",
     "Solid timeline — Olympus producers' planning meetings are perfect for that horizon."),
    ("Smart to start early — gives Richard time to learn what you actually want, including off-market inventory that doesn't show up on search filters.",
     "Smart to start early — gives the right Olympus producer time to learn what you actually want, including off-market inventory and pocket listings that don't show up on search filters."),
    ("Selling luxury is its own discipline — most agents under-price luxury homes because they don't have comps for properties that rarely trade. Richard's brokerage focuses on luxury specifically. The two questions every luxury seller asks first: <em>\"What's the right number?\"</em> and <em>\"Who's the right buyer?\"</em><br><br>Both get answered properly in a 60-minute listing consultation at your home — Richard walks the property, pulls real luxury comps, and gives you a real strategy. Free, no obligation. What's your timeline?",
     "Selling at any price point benefits from agent specialization. Olympus producers cover luxury (where the comp work is harder), investor properties (where ROI math matters more than emotional pricing), traditional residential, and vacation homes. The two questions every seller asks first: <em>\"What's the right number?\"</em> and <em>\"Who's the right buyer?\"</em><br><br>Both get answered in a 60-minute listing consultation at your home with the producer who specializes in your segment. Free, no obligation. What's your timeline?"),
    ("Understood — Richard can be at your door this week with comps and a positioning strategy.",
     "Understood — your matched Olympus producer can be at your door this week with comps and a positioning strategy."),
    ("Perfect timeline — Richard can plan the staging, photography, and luxury-buyer positioning properly with that runway.",
     "Perfect timeline — your producer can plan the staging, photography, and buyer positioning properly with that runway."),
    ("Smart to know your number before deciding — Richard will give you an honest luxury valuation, not a hype number.",
     "Smart to know your number before deciding — your matched producer will give you an honest valuation, not a hype number."),
    ("First-time luxury buyers face a different challenge than the typical first-timer — usually it's financing structure (jumbo, foreign income, asset-based) and understanding what differentiates luxury inventory from over-priced traditional homes. Richard walks first-time luxury buyers through this personally.",
     "First-time buyers (luxury or otherwise) face their own learning curve — financing structure, what differentiates good inventory from over-priced listings, what sellers look for in offers. Olympus has producers who specialize in first-time-buyer education with no pressure on the timeline."),
    ("`Of course — type your question and I'll do my best. If it's something Richard needs to weigh in on personally (specific properties, offer strategy, neighborhood specifics), I'll route it to him and he'll get back to you in the morning.`",
     "`Of course — type your question. If it's about a specific market or property, I'll route it to the producer who knows that area best and they'll get back to you in the morning.`"),
    ("Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Richard's calendar?",
     "Perfect. Let me hold ${timeMap[value]}. What's your first name and roughly which area you're focused on so I can match you with the right producer?"),
    ('<div class="booking-icon">P</div>', '<div class="booking-icon">O</div>'),
    ('<span class="value">Richard Palmano</span>', '<span class="value">Matched Olympus Producer</span>'),
    ('<span class="value">150 N Orlando Ave, Winter Park</span>',
     '<span class="value">Olympus HQ · Montverde, FL</span>'),
    ("(407) 232-5801", "(407) 469-2000"),
    ("Richard will text you a confirmation by 9 AM.",
     "Your matched Olympus producer will text a confirmation by 9 AM."),
    ("Richard wants to pull comps before the visit.",
     "The producer wants to pull comps before the visit."),
    ("Richard will reach out", "Your matched producer will reach out"),
    ("Richard has been notified", "The brokerage has notified the right producer"),
    ("`No problem. Richard has openings", "`No problem. Olympus has openings"),
    ("palmanogroup.com", "olympusexecutiverealty.com"),
    ("private luxury lenders", "preferred lenders across the buyer spectrum"),
    ("Richard", "the Olympus team"),
]
OLYMPUS_CLEANUP = [
    ("Richard", "the Olympus team"),
    ("Palmano", "Olympus"),
]

# ---- ADRIATICO TRATTORIA ITALIANA — College Park (base: bacan.html) ----
# Marco Cudazzo (chef) + Rosetta Cudazzo (owner), old-world Italian, fresh pasta,
# Adriatic coast, 2417 Edgewater Drive, Mon-Sat 5pm-8:30pm last seating
ADRIATICO_SUBS = [
    ("BACÁN — Reservations & Private Dining Concierge | Powered by Velo AI",
     "Adriatico Trattoria Italiana — Reservations Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for BACÁN at Lake Nona Wave Hotel.",
     "This is a live demo built by Velo AI for Adriatico Trattoria Italiana"),
    ("Lake Nona, FL · Michelin-Recognized",
     "College Park, Orlando · Old-World Italian"),
    ('<h1 class="practice-name">BACÁN</h1>',
     '<h1 class="practice-name">Adriatico Trattoria</h1>'),
    ('<p class="practice-doctor">Chef Guillaume Robin</p>',
     '<p class="practice-doctor">Chef Marco &amp; Rosetta Cudazzo</p>'),
    ("BACÁN runs a refined dinner service where the team can't always pause to answer the phone — but reservations, dietary inquiries, and private dining requests get captured around the clock.",
     "Adriatico is a true trattoria — Marco at the pass running fresh pasta, Rosetta in the dining room making sure every guest is taken care of. The phone gets in the way of both jobs. The concierge captures reservations, dietary planning, and private events around the clock."),
    ("6500 Tavistock Lakes Blvd<br>Lake Nona, FL 32827",
     "2417 Edgewater Drive<br>Orlando, FL 32804"),
    ("(407) 675-2000", "(407) 428-0044"),
    ("Tue–Sat · Dinner Service", "Mon–Sat 5p · Last Seating 8:30p"),
    ("<strong>BACÁN Concierge</strong> · Available 24/7",
     "<strong>Adriatico Concierge</strong> · Available 24/7"),
    ("Hotel guest or private dining inquiry? Chef Robin's team is notified directly.",
     "Special occasion or private dinner? Marco and Rosetta will be notified directly."),
    ("Welcome to BACÁN. The dining room is mid-service and the team can't always pick up — but I'm here. I can take reservations, scope private dining, walk you through dietary considerations, and have anything time-sensitive in front of Chef Robin before service tomorrow.",
     "Welcome to Adriatico. Marco's at the pass — fresh pasta is made-to-order, so he can't step away mid-service to take the phone. Rosetta's running the room. I'm here in their place: I can take reservations, walk through the menu and any dietary considerations, scope private events, and have anything time-sensitive in front of them before tomorrow's dinner service."),
    ("{ label: '🍽️ Reservation', value: 'emergency' },\n        { label: '🥂 Private dining or events', value: 'high-value' },\n        { label: '🥗 Menu / dietary question', value: 'new-patient' },\n        { label: '❓ Hotel guest concierge', value: 'question' }",
     "{ label: '🍝 Reservation', value: 'emergency' },\n        { label: '🥂 Private event / large party', value: 'high-value' },\n        { label: '🍷 Wine or menu question', value: 'new-patient' },\n        { label: '❓ A general question', value: 'question' }"),
    ("Of course — type your question. The menu rotates seasonally so I'll have current info on what's running. Dietary stuff (the kitchen handles vegetarian and gluten-free with reasonable notice), open-kitchen-specific questions, or anything about an event — I can usually answer right now.",
     "Of course — Adriatico's menu features hand-made fresh pasta and old-world Italian cooking inspired by the Adriatic coast. I can walk through the regions represented, the wine program (Italy-focused), dietary accommodations Marco can prepare with notice, or specific dishes. What would help?"),
    ("Private dining at BACÁN can accommodate intimate dinners up to full restaurant buyouts for hotel events. What kind of event are you considering?",
     "Private events at Adriatico are intimate by nature — the trattoria is meant for tables of friends, not banquet rooms. Most private events are 8-20 guests with a curated multi-course Italian dinner Marco builds for the occasion. What kind of event are you considering?"),
    ("Private dining at BACÁN starts at parties of 8 with a curated tasting menu, and scales to full restaurant buyouts. Pricing is typically $125-225 per person depending on the menu and beverage program. Chef Robin's team does a planning call before quoting — that way the menu fits the event, not the other way around.",
     "Private events at Adriatico start at 8 guests with a four-to-six course Italian progression. Pricing typically lands $75-125 per person depending on the menu and wine pairings. Marco does a planning call before quoting so the menu actually reflects what you and your guests will love (and what's freshest that week)."),
    ("Welcome — are you a Lake Nona Wave Hotel guest looking to book at BACÁN? I can hold a table prioritized for hotel guests, walk through the menu, or answer hours and dress code questions. What can I help with?",
     "Of course — type your question. Anything about the menu, the wine program, dietary accommodations, hours, dress code, or special occasions — I can usually answer right now."),
    ("(407) 675-2000", "(407) 428-0044"),
    ('<div class="booking-icon">B</div>', '<div class="booking-icon">A</div>'),
    ('<span class="value">BACÁN Team</span>', '<span class="value">Marco &amp; Rosetta</span>'),
    ('<span class="value">6500 Tavistock Lakes Blvd, Lake Nona</span>',
     '<span class="value">2417 Edgewater Drive, Orlando</span>'),
    ("Chef Robin", "Marco"),
    ("BACÁN", "Adriatico"),
]
ADRIATICO_CLEANUP = [
    ("bacanlakenona.com", "adriatico-trattoria.com"),
]

# ---- SUSANA'S CAFE — Latin breakfast cafe in Kissimmee (base: pigfloyds.html) ----
# 100-year-old Craftsman house, 18 S Orlando Ave, Latin-inspired (arepas, tequeños,
# Venezuelan empanadas, Cuban sandwich) + American breakfast, Costa Rican coffee,
# Best Breakfast Orlando 2024, Mon-Sun 8am-3pm, dog-friendly outdoor
SUSANAS_SUBS = [
    ("Pig Floyd's Urban Barbakoa — Reservations & Catering Concierge | Powered by Velo AI",
     "Susana's Café — Reservations &amp; Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Pig Floyd's Urban Barbakoa.",
     "This is a live demo built by Velo AI for Susana's Café"),
    ("Mills 50, Orlando · Slow-Smoked",
     "Downtown Kissimmee · Best Breakfast 2024"),
    ("<h1 class=\"practice-name\">Pig Floyd's Urban Barbakoa</h1>",
     "<h1 class=\"practice-name\">Susana's Café</h1>"),
    ('<p class="practice-doctor">Thomas, Owner</p>',
     "<p class=\"practice-doctor\">Susana, Owner</p>"),
    ("Pig Floyd's runs hot during dinner service and the team can't always pause to answer calls — but reservations, takeout, and catering inquiries get captured around the clock.",
     "Susana's runs in a 100-year-old Craftsman house in downtown Kissimmee — Susana behind the counter, the only Costa Rican vandola brewing in Osceola County humming. The phone is the last thing she should be picking up during morning rush. The concierge captures large-party reservations, catering, and questions any time of day."),
    ("1326 N Mills Ave<br>Orlando, FL 32803",
     "18 S Orlando Ave<br>Kissimmee, FL 34741"),
    ("(407) 203-0866", "(407) 201-2627"),
    ("Tue–Sun · Lunch & Dinner Service",
     "Mon–Sun 8a–3p · Indoor / Outdoor / Dog-Friendly"),
    ("<strong>Pig Floyd's Concierge</strong> · Available 24/7",
     "<strong>Susana's Concierge</strong> · Available 24/7"),
    ("Catering or large party? Thomas will be notified directly for time-sensitive bookings.",
     "Large party or catering inquiry? Susana will be notified directly."),
    ("Welcome to Pig Floyd's. The dining room is loud and the smokers are working — the team can't always pick up. I'm the after-hours line: I can take reservations, quote catering, and answer most menu questions before service tomorrow.",
     "Welcome to Susana's Café — winner of Best Breakfast in Orlando 2024. We're in a beautifully preserved Craftsman house at 18 S Orlando Ave. The morning rush keeps Susana behind the counter. I'm here to take reservations for larger parties, walk you through the Latin and American breakfast menus, the freshly ground Costa Rican coffee program, and any catering or event inquiries."),
    ("{ label: '🍽️ Reservation', value: 'emergency' },\n        { label: '🎉 Catering or large party', value: 'high-value' },\n        { label: '🛍️ Pickup or takeout', value: 'new-patient' },\n        { label: '❓ Menu / hours question', value: 'question' }",
     "{ label: '☕ Large party reservation', value: 'emergency' },\n        { label: '🎉 Catering or event order', value: 'high-value' },\n        { label: '🛍️ Pickup or takeout', value: 'new-patient' },\n        { label: '❓ Menu / hours question', value: 'question' }"),
    ("Awesome — let's get you a table.",
     "Susana's seats parties up to about 12 inside and a few more on the dog-friendly patio."),
    ("Got it — same-night reservations get tight quickly during peak service. Let me check the books and get back to you. While I do that, can I get your first name, party size, and a phone number? If you're aiming for tonight in the next hour, please also call (407) 203-0866 directly — we hold a few walk-in seats.",
     "Mornings get busy fast — weekends especially. Let me check the books and get back to you. While I do that, can I get your first name, party size, and a phone number? If you're aiming for tomorrow within a few hours, please also call (407) 201-2627 directly — there are usually a few walk-in seats."),
    ("Got it. The team typically has good availability mid-week — Tuesday and Wednesday have the most flexibility for parties of 4 or more.<br><br>What's your first name and party size? I'll have someone pre-confirm with you in the morning.",
     "Got it. Mid-week mornings are usually quieter than weekends. Tuesday or Wednesday around 9:30-10am has the most flexibility for parties of 6 or more.<br><br>What's your first name and party size? I'll have Susana confirm with you in the morning."),
    ("Catering is one of Pig Floyd's strengths — the smoker doesn't sleep, so we can scale up for almost any event. What kind of event?",
     "Susana caters Latin breakfast events, brunches, and workplace catering — empanadas (multiple varieties), tequeños, Cuban sandwiches, the freshly ground Costa Rican coffee setup. What kind of event?"),
    ("Pig Floyd's catering ranges from BBQ trays for 10 people up to full-service events for 200+. Pricing usually lands $18-32 per person depending on protein mix and service style. Thomas does a free 15-minute call to scope events before quoting — that way the quote is real, not generic.",
     "Susana's catering ranges from breakfast platters for 10 people up to full breakfast/brunch service for 100+. Pricing usually lands $14-22 per person depending on the menu mix (Latin only, mixed Latin/American, with or without coffee service). Susana does a quick scoping call before quoting — that way the quote actually fits your event."),
    ("'implants': 'corporate catering',\n      'invisalign': 'wedding catering',\n      'both': 'family-style catering'",
     "'implants': 'workplace breakfast catering',\n      'invisalign': 'event / brunch catering',\n      'both': 'mixed Latin / American catering'"),
    ("Most clients asking about ${txt} are wondering: <em>\"How many people can you feed?\"</em> and <em>\"What's it going to cost?\"</em><br><br>Pig Floyd's catering ranges from BBQ trays for 10 people up to full-service events for 200+. Pricing usually lands $18-32 per person depending on protein mix and service style. Thomas does a free 15-minute call to scope events before quoting — that way the quote is real, not generic.",
     "Most clients asking about ${txt} are wondering: <em>\"What's the menu?\"</em> and <em>\"What's it going to cost?\"</em><br><br>Susana builds menus around what the group will love — typically a mix of Venezuelan empanadas, cheese tequeños (with optional guava jam), Cuban sandwiches, fresh fruit, and Costa Rican coffee. Pricing usually lands $14-22 per person. She does a 15-minute call to scope events before quoting."),
    ("Pickup orders go through our online system — fastest way is to order at pigfloyds.com/order or call (407) 203-0866 during service. If you want me to text you the link or hold a name in the system for tomorrow, what's your first name?",
     "Pickup is easiest by calling (407) 201-2627 during morning hours — Susana or someone behind the counter will take it directly. If you want me to text the menu link to your phone, or hold a name for a pickup tomorrow, what's your first name?"),
    ("Of course — type your question. Hours, menu items, dietary stuff (we have vegan smoke options), or anything specific to a dish — I can usually answer right now.",
     "Of course — type your question. Hours, menu items, dietary stuff (vegetarian-friendly menu, gluten-free options), Costa Rican coffee questions (we use a vandola — only one in Osceola County), or anything specific to a dish — I can usually answer right now."),
    ('<div class="booking-icon">P</div>', '<div class="booking-icon">S</div>'),
    ("<span class=\"value\">Pig Floyd's Team</span>",
     "<span class=\"value\">Susana</span>"),
    ('<span class="value">1326 N Mills Ave, Orlando</span>',
     '<span class="value">18 S Orlando Ave, Kissimmee</span>'),
    ("'implants': 'Corporate Catering Consult',\n          'invisalign': 'Event Catering Consult',\n          'both': 'Family Catering Consult',\n          'emergency': 'Reservation'",
     "'implants': 'Workplace Breakfast Catering Consult',\n          'invisalign': 'Event Brunch Catering Consult',\n          'both': 'Mixed Latin/American Catering Consult',\n          'emergency': 'Large Party Reservation'"),
    ("Perfect. Here's the hold I'm creating for the Pig Floyd's team:",
     "Perfect. Here's the hold I'm creating for Susana:"),
    ("You're all set, ${memory.name}. The team has been notified — you'll get a confirmation text from <strong>(407) 203-0866</strong> by mid-morning.<br><br>Take care tonight — see you at the smoker.",
     "You're all set, ${memory.name}. Susana will text you from <strong>(407) 201-2627</strong> tomorrow morning to confirm.<br><br>See you at the cafe."),
    ("No problem. Pig Floyd's has tables available Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM — which works best?",
     "No problem. Susana has tables Tuesday at 9:30 AM, Wednesday at 10:30 AM, or Saturday at 11 AM — which works best?"),
    ("(407) 203-0866", "(407) 201-2627"),
    ("Pig Floyd's", "Susana's"),
    ("Thomas", "Susana"),
]
SUSANAS_CLEANUP = [
    ("Pig Floyd", "Susana"),
    ("Thomas", "Susana"),
]

# ---- LUSH LASH — Lash studio, Altamonte Springs (base: goldie.html) ----
# 21+ years in business, "Orlando's Premier Place for Lash Enhancements", proprietary
# Lush Lash Adhesive (4-6 week hold), 250+ extensions per eye minimum, lashes-only
LUSHLASH_SUBS = [
    ("Goldie Salon — After-Hours Booking Concierge | Powered by Velo AI",
     "Lush Lash — Lash Booking Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Goldie Salon.",
     "This is a live demo built by Velo AI for Lush Lash."),
    ("Lake Mary, Florida · Luxury Hair",
     "Altamonte Springs, Florida · 21+ Years · Lashes Only"),
    ('<h1 class="practice-name">Goldie Salon</h1>',
     '<h1 class="practice-name">Lush Lash</h1>'),
    ('<p class="practice-doctor">The Goldie Team</p>',
     "<p class=\"practice-doctor\">Orlando's Premier Place for Lash Enhancements</p>"),
    ("Goldie's stylists are committed to giving every client a seamless experience — from the first DM at 11pm to the final blowout. The booking line never sleeps.",
     "21 years specializing in lash enhancements only, with proprietary Lush Lash Adhesive (4-6 week hold) and Lush Lash Techniques. Minimum 250 extensions per eye — that's the standard, not the upsell. Bookings come in around the clock; the concierge makes sure every one is captured."),
    ("(321) 363-1233", "(407) 772-4000"),
    ("Tue–Sat · By Appointment", "By Appointment · 21+ Years"),
    ("<strong>Goldie Concierge</strong> · Available 24/7",
     "<strong>Lush Lash Concierge</strong> · Available 24/7"),
    ("A regular at Goldie? Your stylist will be notified directly for time-sensitive bookings.",
     "A regular at Lush Lash? Your lash artist will be notified directly for time-sensitive bookings."),
    ("Welcome to Goldie. Your stylist's chair is empty for the night, but I'm the after-hours booking concierge — I can quote services, hold appointments, and answer most questions before you go to sleep.",
     "Welcome to Lush Lash — Orlando's premier lash studio for 21+ years. Your lash artist is wrapped for the night, but I'm here — I can quote services across full sets / fills / removals, walk you through the difference between classic / hybrid / volume, hold appointments, and answer questions about the proprietary Lush Lash Adhesive (4-6 week hold) before you go to sleep."),
    # Chips — lash-only specific
    ("{ label: '💇 Cut or style', value: 'emergency' },\n        { label: '🎨 Color, balayage, or highlights', value: 'high-value' },\n        { label: '✨ Extensions or treatments', value: 'new-patient' },\n        { label: '❓ A pricing question', value: 'question' }",
     "{ label: '💎 Full set (new client)', value: 'emergency' },\n        { label: '🔁 Fill / refresh', value: 'high-value' },\n        { label: '🌟 Mega volume / wedding', value: 'new-patient' },\n        { label: '❓ A pricing question', value: 'question' }"),
    ("'emergency': 'I want a cut or style',\n      'high-value': \"I want color, balayage, or highlights\",\n      'new-patient': \"I want extensions or a treatment\"",
     "'emergency': \"I want a full set (new client)\",\n      'high-value': \"I want a fill or refresh\",\n      'new-patient': \"I want mega volume or a wedding set\""),
    # Full set path (was emergency/cut)
    ("// CUT/STYLE PATH ----------------------------------\n    if (value === 'emergency') {\n      memory.concern = 'cut-style';\n      await addBotMessage(\n        `Love that. Cut and style is the best place to start — most of Goldie's clients first came in for a simple cut and stayed for everything else.`,\n        900\n      );\n      await addBotMessage(\n        `Quick question so I know how to prioritize — when do you need it by?`,\n        1100,\n        [\n          { label: '🔴 This week — special event', value: 'severe' },\n          { label: '🟡 Within 2 weeks', value: 'moderate' },\n          { label: '🟢 Whenever there\\'s availability', value: 'mild' }\n        ]\n      );\n      return;\n    }",
     "// FULL SET PATH ----------------------------------\n    if (value === 'emergency') {\n      memory.concern = 'fullset';\n      await addBotMessage(\n        `Welcome — first lash set is its own moment. Plan for ~2 hours, and the proprietary Lush Lash Adhesive will hold for 4-6 weeks before your first fill.`,\n        900\n      );\n      await addBotMessage(\n        `Quick question — what kind of look are you going for?`,\n        1100,\n        [\n          { label: '🍃 Natural / classic', value: 'severe' },\n          { label: '✨ Hybrid (mixed look)', value: 'moderate' },\n          { label: '💎 Full volume / dramatic', value: 'mild' }\n        ]\n      );\n      return;\n    }"),
    ("Got it — special event urgency. The team usually has a couple priority slots reserved each week for events. Let me get you on the calendar.<br><br>Can I get your first name and best phone number? Whatever the event is, we'll make sure you walk in feeling like the moment matters.",
     "Got it — classic style is a great place to start. Most first-time clients book classic and graduate to hybrid or volume on the second visit when they're ready for more drama.<br><br>Can I get your first name and best phone number? I'll have your lash artist confirm in the morning."),
    ("Perfect timeline. Goldie's stylists keep mid-week slots open for new clients — Tuesday or Thursday work best.<br><br>What's your first name? I'll have someone pre-confirm with you by tomorrow morning.",
     "Hybrid sets are the most-booked at Lush Lash — they balance natural with dramatic and last well between fills. Tuesday or Thursday have the most flexibility for new clients.<br><br>What's your first name? I'll have your lash artist pre-confirm with you by tomorrow morning."),
    # Fill path (was high-value/color)
    ("// COLOR PATH ----------\n    if (value === 'high-value') {\n      memory.concern = 'color';\n      await addBotMessage(\n        `Smart move to reach out before you book — Goldie's colorists specialize in luxury color and would much rather hear what you're going for before you arrive than try to fix something rushed.<br><br>What kind of color are you thinking?`,\n        900,\n        [\n          { label: '🌟 Balayage', value: 'implants' },\n          { label: '✨ Full highlights', value: 'invisalign' },\n          { label: '🎨 Color correction', value: 'both' }\n        ]\n      );\n      return;\n    }",
     "// FILL PATH ----------\n    if (value === 'high-value') {\n      memory.concern = 'fill';\n      await addBotMessage(\n        `Smart to book the fill before you actually need it — fills run shorter than full sets (60-90 min) but rebook fast. The Lush Lash Adhesive holds 4-6 weeks, so you have flexibility.<br><br>How long since your last appointment?`,\n        900,\n        [\n          { label: '🟢 Less than 3 weeks', value: 'implants' },\n          { label: '🟡 3-5 weeks', value: 'invisalign' },\n          { label: '🔴 6+ weeks (fresh full set)', value: 'both' }\n        ]\n      );\n      return;\n    }"),
    ("if (value === 'implants' || value === 'invisalign' || value === 'both') {\n      memory.treatmentInterest = value;\n      const txt = value === 'implants' ? 'classic lashes' : value === 'invisalign' ? 'volume lashes' : 'a brow service';",
     "if (value === 'implants' || value === 'invisalign' || value === 'both') {\n      memory.treatmentInterest = value;\n      const txt = value === 'implants' ? 'a quick refresh fill' : value === 'invisalign' ? 'a standard fill' : 'a fresh full set (instead of a fill)';"),
    ("Most clients booking ${txt} are wondering: <em>\"Will it look natural?\"</em> and <em>\"How long does it last?\"</em><br><br>Both are best answered in a 15-minute consultation — the lash artist looks at your natural lashes, walks through what's realistic for your eye shape and lifestyle, and gives you a real quote and timing before you commit. Want me to hold a slot this week?",
     "Got it — ${txt} books fastest mid-week. Want me to hold a slot this week or next?"),
    # Mega volume / wedding (was extensions)
    ("The Look's spa side handles facials (rejuvenating, anti-wrinkle), microblading, eyebrow tinting, full body waxing, and skincare consultations. The estheticians do continuing education quarterly so the techniques stay current. What's your first name? I'll have the right specialist follow up tomorrow morning.",
     "Mega volume and wedding lash sets are their own art form — they take longer (2.5-3 hours) and book out further than standard sets. For weddings, most clients book the trial 4-6 weeks ahead so the actual wedding-day appointment is purely a fill. What's your first name? I'll have your lash artist confirm with you tomorrow morning."),
    ("(321) 363-1233", "(407) 772-4000"),
    ('<div class="booking-icon">G</div>', '<div class="booking-icon">L</div>'),
    ('<span class="value">Goldie Stylist</span>',
     '<span class="value">Lush Lash Artist</span>'),
    ("Goldie", "Lush Lash"),
]
LUSHLASH_CLEANUP = [
    ("Goldie", "Lush Lash"),
]

# ---- VENETIAN POINTE DENTISTRY — Dr. Phillips (base: wayside.html) ----
# Dr. Richard C. Rampi (founder, UF DMD, est. 1987) + Dr. Richard A. Rampi (implants),
# 38+ yrs, multi-generational, "honest care no pressure", same-day emergency,
# 5940 Turkey Lake Rd, serves Dr. Phillips/Windermere/MetroWest/Bay Hill/Sand Lake
VPDENTAL_SUBS = [
    ("Wayside Family Dental — After-Hours Concierge | Powered by Velo AI",
     "Venetian Pointe Dentistry — After-Hours Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Wayside Family Dental.",
     "This is a live demo built by Velo AI for Venetian Pointe Dentistry."),
    ("Sanford, Florida · Est. 2012",
     "Dr. Phillips, Orlando · Est. 1987 · Multi-Generational"),
    ('<h1 class="practice-name">Wayside Family Dental</h1>',
     '<h1 class="practice-name">Venetian Pointe Dentistry</h1>'),
    ('<p class="practice-doctor">Dr. Lyudmila A. Onyski, DDS</p>',
     '<p class="practice-doctor">Drs. Richard C. Rampi &amp; Richard A. Rampi</p>'),
    ("Dr. Onyski is on call to respond to her patients' needs as soon as possible. As a patient of Wayside, you're never alone.",
     "Dr. Richard C. Rampi founded the practice in 1987. 38+ years later, the same family — Dr. Richard C. and Dr. Richard A. — still leads it, with a long-tenured staff. Patients describe the philosophy as &quot;honest care, no pressure.&quot; That extends to after-hours: no patient gets ignored."),
    ("4907 International Pkwy, Suite 1041<br>Sanford, FL 32771",
     "5940 Turkey Lake Rd<br>Orlando, FL 32819"),
    ("<div>(407) 732-4570</div>", "<div>(407) 352-6959</div>"),
    ("Mon–Thu 8a–5p · Fri 8a–1p",
     "Mon–Fri 8a–5p · Same-Day Emergencies"),
    ("<strong>Wayside Concierge</strong> · Available 24/7",
     "<strong>Venetian Pointe Concierge</strong> · Available 24/7"),
    ("A patient of Wayside? Dr. Onyski will be notified immediately for urgent matters.",
     "A patient of the practice? Dr. Rampi will be notified immediately for urgent matters."),
    ("Good evening — you've reached the after-hours line for Wayside Family Dental. Dr. Onyski is unavailable right now, but I can help with most things and reach her directly if it's urgent.",
     "Good evening — you've reached the after-hours line for Venetian Pointe Dentistry. The practice has served Dr. Phillips, Windermere, MetroWest, Bay Hill, and Sand Lake families since 1987. Both Dr. Rampis are wrapped for the day — but they keep same-day emergency slots, and I can help with most things in the meantime."),
    ("Dr. Onyski has been doing both since 2010, so you're in capable hands.",
     "The Rampi practice has been doing both for decades, with Dr. Richard A. leading implant work using 3D imaging and digital surgical planning. You're in capable hands."),
    ("Dr. Onyski has been welcoming new patients to Wayside since 2012",
     "The Rampi practice has been welcoming new patients to Dr. Phillips since 1987"),
    ("texting Dr. Onyski now — she'll call you back",
     "texting Dr. Rampi now — he'll call you back"),
    ("Dr. Onyski will want to see you first thing — she keeps emergency slots",
     "Dr. Rampi will want to see you first thing — the practice keeps same-day emergency slots"),
    ("Dr. Onyski's office", "the office"),
    ("Dr. Onyski has been notified", "Dr. Rampi has been notified"),
    ("Dr. Onyski opens new-patient slots", "The practice opens new-patient slots"),
    ("Dr. Onyski has openings", "Dr. Rampi has openings"),
    ("Dr. Onyski needs to weigh in", "Dr. Rampi needs to weigh in"),
    ("she'll call", "he'll call"),
    ("she keeps emergency slots", "he keeps emergency slots"),
    ("she calls", "he calls"),
    ('<div class="booking-icon">W</div>', '<div class="booking-icon">V</div>'),
    ('<span class="value">Dr. Lyudmila A. Onyski</span>',
     '<span class="value">Dr. Richard Rampi</span>'),
    ('<span class="value">4907 International Pkwy, Suite 1041</span>',
     '<span class="value">5940 Turkey Lake Rd, Orlando</span>'),
    ("(407) 732-4570", "(407) 352-6959"),
    ("Dr. Onyski", "Dr. Rampi"),
    ("Wayside", "Venetian Pointe"),
]
VPDENTAL_CLEANUP = [
    ("Wayside", "Venetian Pointe"),
    ("Onyski", "Rampi"),
]

# ============================================================================
# ROUND 4 — 7 more prospects with deep research data
# ============================================================================

# ---- FORWARD LAW FIRM — Business law / IP / M&A, Orlando (base: lathamluna.html) ----
# Real data: Philip K. Calandrino (founder/CEO, AV-Preeminent, 20+ yrs) + Jared A. Mangum,
# 10 practice areas, "preventative approach" philosophy, 1615 Woodward St
FORWARD_SUBS = [
    ("Latham Luna — After-Hours Intake | Powered by Velo AI",
     "Forward Law Firm — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Latham Luna",
     "This is a live demo built by Velo AI for Forward Law Firm"),
    ("Downtown Orlando · Est. 1996",
     "Orlando, Florida · AV-Preeminent · 20+ Years"),
    ('<h1 class="practice-name">Latham Luna</h1>',
     '<h1 class="practice-name">Forward Law Firm</h1>'),
    ('<p class="practice-doctor">Daniel Velasquez, Esq.</p>',
     '<p class="practice-doctor">Philip K. Calandrino &amp; Jared A. Mangum, Esq.</p>'),
    ("<h4>World-Class Counsel · Small-Town Service</h4>",
     "<h4>Preventative Counsel, Not Reactive</h4>"),
    ("Latham Luna is a downtown Orlando boutique with eleven practice areas — bankruptcy, construction, commercial litigation, hospitality, aviation. The firm's positioning is &quot;World-Class Counsel, Small-Town Service.&quot; Daniel is committed to being available when business actually moves, not just when the office is open.",
     "Forward Law Firm is built on a specific philosophy: business law attorneys should prevent fires, not just put them out. The firm covers ten practice areas — business formation, M&amp;A, IP, franchising, employment, commercial litigation, contracts. Phil is committed to being available when business actually moves."),
    ("Good evening — you've reached the after-hours line for Latham Luna in downtown Orlando. The firm covers eleven practice areas; Daniel chairs the Aviation Department and is a Bankruptcy Partner. He's wrapped for the day, but I can take down what's going on and route it to him or another attorney depending on the matter.",
     "Good evening — you've reached the after-hours line for Forward Law Firm. The firm is AV-Preeminent rated and covers ten business law practice areas — business formation, contracts, M&amp;A, IP, franchising, employment, and commercial real estate. Phil and Jared are wrapped for the day, but I can take down what's going on and route it to whichever attorney fits."),
    ("Daniel and the Latham Luna team handle business, bankruptcy, and construction matters every week",
     "Phil, Jared, and the Forward team handle business matters every week"),
    ("Business disputes are core territory for Latham Luna — the firm's been doing this since 1996, with five attorneys in Florida Super Lawyers and six in Best Lawyers in America. Daniel handles bankruptcy specifically, and other partners cover commercial litigation, employment, and corporate matters. The two things that help the team move fast: what's the dispute, and whether there's a deadline anywhere in the next two weeks.",
     "Business disputes are core territory for Forward — but Phil's preference, by philosophy, is to catch them before they're disputes. Many of the after-hours calls the firm receives are pre-dispute moments: a contract about to be signed that has a problem, a partner conversation that's getting tense, a vendor situation that's heading toward litigation. The two things that help the team move fast: what's happening, and whether there's a deadline or signature window in the next two weeks."),
    ("Construction matters move on tight statutory deadlines — Florida lien notices, payment bond claims, contractor disputes. Latham Luna has a dedicated construction practice and the first thing the team checks is whether you're inside the statutory window.",
     "Real estate transactions, contracts, and franchising matters often move on tight windows — closing dates, contract signature deadlines, franchise disclosure timelines. Forward handles these regularly, and the first thing the team checks is whether you're inside the window."),
    ("Bankruptcy and foreclosure are Daniel's specialty — he's a Bankruptcy Partner at the firm. Filing windows, automatic stays, 341 meetings, and the difference between Chapter 7 vs Chapter 11 vs Chapter 13 are all conversations he has every week. The first thing he wants to know is your timeline urgency.",
     "Employment law, commercial real estate, and securities matters all surface unpredictably. Forward's preventative philosophy means the team would rather hear about it early — even if it feels too small to call about — than after the dispute has escalated. The first thing the team wants to know is your timeline."),
    # Address/contact
    ("111 N Magnolia Ave, Suite 1400<br>Orlando, FL 32801",
     "1615 Woodward Street<br>Orlando, FL 32803"),
    ("(407) 481-5800", "(407) 621-4200"),
    ('<span class="value">Daniel Velasquez, Esq.</span>',
     '<span class="value">Philip Calandrino or Jared Mangum, Esq.</span>'),
    ('<span class="value">111 N Magnolia Ave, Orlando</span>',
     '<span class="value">1615 Woodward Street, Orlando</span>'),
    # Matter map
    ("'business': 'Business Dispute Consultation',\n          'construction': 'Construction Law Consultation',\n          'bankruptcy': 'Bankruptcy / Foreclosure Consultation',\n          'question': 'General Consultation'",
     "'business': 'Business Matter Consultation',\n          'construction': 'Real Estate / Contract Consult',\n          'bankruptcy': 'Employment / Securities Consult',\n          'question': 'General Consultation'"),
    ("Daniel ", "Phil "),
    ("Daniel.", "Phil."),
    ("Daniel,", "Phil,"),
    ("Daniel's", "Phil's"),
    ("Latham Luna", "Forward Law Firm"),
]
FORWARD_CLEANUP = [
    ("Daniel", "the Forward team"),
    ("Latham", "Forward"),
]

# ---- KANE AND KOLTUN — Estate/tax/corporate, Maitland (base: ragland.html) ----
# Real data: Founded 1997, Steven H. Kane (Board Certified Wills/Trusts/Estates +
# UF JD with honors '80 + LLM Taxation Miami '83 + CPA — rare combo!) + Jeffrey Koltun,
# AV-rated, 28+ years
KANE_SUBS = [
    ("Lance A. Ragland, P.A. — After-Hours Intake | Powered by Velo AI",
     "Kane &amp; Koltun — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Lance A. Ragland, P.A.",
     "This is a live demo built by Velo AI for Kane &amp; Koltun"),
    ("Winter Springs, Florida · Est. 2015",
     "Maitland, Florida · Est. 1997 · Board Certified · CPA"),
    ('<h1 class="practice-name">Lance A. Ragland, P.A.</h1>',
     '<h1 class="practice-name">Kane &amp; Koltun</h1>'),
    ('<p class="practice-doctor">Lance A. Ragland, Esq.</p>',
     '<p class="practice-doctor">Steven H. Kane &amp; Jeffrey M. Koltun, Esq.</p>'),
    ("<h4>Available When You Need Him</h4>",
     "<h4>The Rare Lawyer-CPA Combination</h4>"),
    ("Estate matters rarely surface during business hours. Lance is committed to being there for clients during life's most difficult transitions. You're never alone.",
     "Most estate planning attorneys recommend you talk to your CPA. Steven Kane IS a CPA — alongside being Board Certified by the Florida Bar in Wills, Trusts, and Estates and holding an LLM in Taxation. That combination shows up in how the firm handles complex estate, tax, and corporate matters. You're never alone."),
    ("5750 Canton Cove<br>Winter Springs, FL 32708",
     "150 Spartan Drive<br>Maitland, FL 32751"),
    ("(407) 960-6069", "(407) 661-1177"),
    ("By Appointment · Mon–Fri 9a–5p", "Mon–Fri 9a–5p · 28+ Years"),
    ("<strong>Ragland Intake</strong> · Available 24/7",
     "<strong>Kane &amp; Koltun Intake</strong> · Available 24/7"),
    ("A current client of Lance's? He'll be notified directly for urgent matters.",
     "A current client? Steven or Jeffrey will be notified directly for urgent matters."),
    ("Good evening — you've reached the after-hours line for the Law Offices of Lance A. Ragland. Lance focuses entirely on estate planning, probate, and trust matters. He's unavailable right now, but I can take down what's on your mind and get him to reach back out.",
     "Good evening — you've reached the after-hours line for Kane &amp; Koltun in Maitland. The firm has been practicing since 1997. Steven Kane is Board Certified by the Florida Bar in Wills, Trusts &amp; Estates, holds an LLM in Taxation, and is also a CPA — that combination matters when estate planning involves tax complexity. Jeff Koltun and Steven are wrapped for the day, but I can take down what's on your mind."),
    # Same chip set works (estate/probate/poa/question) but reframe
    ("if (value === 'probate') {\n      memory.matter = 'probate';\n      await addBotMessage(\n        `I'm so sorry for your loss. Please take whatever time you need.<br><br>Lance has guided families through probate for nearly thirty years, and most of what feels overwhelming right now has a clear path forward. The two things that help him move quickly when he calls you back: who passed, and whether they had a will.`,",
     "if (value === 'probate') {\n      memory.matter = 'probate';\n      await addBotMessage(\n        `I'm so sorry for your loss. Please take whatever time you need.<br><br>Steven has guided families through probate for 28+ years — and because he's also a CPA, he handles the tax side (estate tax returns, basis adjustments, IRA rollovers) without bouncing you to a separate accountant. The two things that help him move quickly: who passed, and whether they had any documents in place.`,"),
    ("if (value === 'planning') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart of you to think about this — most people put off estate planning for years and regret the procrastination. Lance has been doing wills, trusts, and estate plans exclusively since 2015, so this is exactly his bread and butter.<br><br>Most clients in your shoes are weighing one of two things: <em>\"Do I just need a will, or do I need a trust?\"</em> and <em>\"What's this going to cost me?\"</em><br><br>Both are answered properly in a one-hour consult — Lance reviews your situation, walks you through the difference, and gives you a flat-fee quote before you commit to anything. Want me to hold a slot this week or next?`,",
     "if (value === 'planning') {\n      memory.matter = 'planning';\n      await addBotMessage(\n        `Smart of you to think about this — and Steven's lawyer-CPA-Board-Certified background means estate planning at Kane &amp; Koltun isn't just &quot;will or trust?&quot; It's also tax-efficient asset protection, deferred compensation structuring, and corporate-and-personal coordination if you own a business.<br><br>Most clients are weighing two things: <em>\"What structure actually fits my situation?\"</em> and <em>\"What's this going to cost?\"</em><br><br>Both are answered in a one-hour consult. Want me to hold a slot this week or next?`,"),
    ("if (value === 'poa') {\n      memory.matter = 'poa';\n      await addBotMessage(\n        `These conversations are hard — usually they come up because someone in the family is going through a health change. Lance can put together a power of attorney and healthcare surrogate quickly, often within a few days if needed.<br><br>Just so I get the right urgency to him: is this for an immediate situation, or planning ahead?`,",
     "if (value === 'poa') {\n      memory.matter = 'poa';\n      await addBotMessage(\n        `These conversations are hard — usually they come up because someone in the family is going through a health change. Steven and Jeff can put together a power of attorney and healthcare surrogate quickly, often within a few days if needed.<br><br>Just so I get the right urgency to them: is this for an immediate situation, or planning ahead?`,"),
    ('<div class="booking-icon">L</div>', '<div class="booking-icon">K</div>'),
    ('<span class="value">Lance A. Ragland, Esq.</span>',
     '<span class="value">Steven Kane or Jeffrey Koltun, Esq.</span>'),
    ('<span class="value">5750 Canton Cove, Winter Springs</span>',
     '<span class="value">150 Spartan Drive, Maitland</span>'),
    ("(407) 960-6069", "(407) 661-1177"),
    ("Lance has been notified", "The firm has been notified"),
    ("Lance will reach out", "Steven or Jeffrey will reach out"),
    ("Lance ", "the team "),
    ("Lance's", "the team's"),
    ("Lance.", "the team."),
    ("Lance,", "the team,"),
    ("his office (Debbie)", "the firm's paralegal"),
]
KANE_CLEANUP = [
    ("Lance", "the team"),
    ("Ragland", "Kane & Koltun"),
]

# ---- ESTATE PLANNING & LEGACY LAW CENTER — Altamonte (base: murphyberglund.html) ----
# Real data: Charles D. Wilder (founder, AV Preeminent, 35+ yrs) + Melissa Moses Parker
# + Nicholas Rubino + Debra Mulligan (admin), proprietary EPLLC Client Portal + iOS app,
# Gun Trusts (unusual!), 13 services, English+Spanish, founded 2003
EPLLC_SUBS = [
    ("Murphy & Berglund — After-Hours Intake | Powered by Velo AI",
     "Estate Planning &amp; Legacy Law Center — After-Hours Intake | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Murphy & Berglund",
     "This is a live demo built by Velo AI for Estate Planning &amp; Legacy Law Center"),
    ("Altamonte Springs, Florida · VA-Accredited · Estate &amp; Elder Law",
     "Altamonte Springs · Est. 2003 · 4-Attorney Team · EN/ES"),
    ('<h1 class="practice-name">Murphy &amp; Berglund</h1>',
     '<h1 class="practice-name">Estate Planning &amp; Legacy Law Center</h1>'),
    ('<p class="practice-doctor">Michelle Berglund-Harper &amp; Jodi Murphy, Esq.</p>',
     '<p class="practice-doctor">Charles D. Wilder · Melissa Moses Parker · Nicholas Rubino, Esq.</p>'),
    ("Estate planning, elder law, and family matters surface at life's hardest transitions — declining health, the death of a parent, a Medicaid eligibility crisis, a Veterans benefits question. Murphy &amp; Berglund is VA-accredited and handles both Medicaid planning and VA aid &amp; attendance. Jodi and Michelle are committed to being there during those moments.",
     "Estate planning, elder law, and Medicaid crisis matters surface at life's hardest transitions. EPLLC has been doing this since 2003 — founder Charles Wilder is AV Preeminent rated with 35+ years of experience, and the firm covers everything from basic wills to Gun Trusts (unusual specialty), Special Needs Planning, and Medicaid Crisis. Bilingual (English/Spanish) staff."),
    ("1101 Douglas Ave<br>Altamonte Springs, FL 32714",
     "711 Ballard Street<br>Altamonte Springs, FL 32701"),
    ("(407) 865-9553", "(407) 647-7526"),
    ("<strong>Murphy &amp; Berglund Intake</strong> · Available 24/7",
     "<strong>EPLLC Intake</strong> · Available 24/7"),
    ("A current client? Michelle or Jodi will be notified directly for urgent matters.",
     "A current client? The right attorney (Charles, Melissa, or Nicholas) will be notified directly."),
    ("Good evening — you've reached the after-hours line for Murphy & Berglund. The firm is VA-accredited and handles estate planning, probate, elder law, Medicaid &amp; VA planning, family law, and probate. Both attorneys are wrapped for the day, but everything you share is confidential. I'll route what's on your mind to whichever attorney fits — Jodi or Michelle — and have them reach back out.",
     "Good evening — you've reached the after-hours line for Estate Planning &amp; Legacy Law Center. The firm has been doing comprehensive legacy planning since 2003. Charles Wilder (founder, AV Preeminent, 35+ years) leads the firm, with Melissa Moses Parker and Nicholas Rubino on the team. Bilingual English/Spanish staff. The team is wrapped for the day, but everything you share is confidential."),
    # Chip cleanup — same set
    # Estate/probate path
    ("I'm sorry — these calls usually come at one of the hardest moments. Jodi handles probate and trust administration directly. She and Michelle have walked over a hundred families through the post-loss paperwork — the will or trust contest, asset retitling, creditor claims, the steps that nobody explains. The two things that help her move quickly: who passed, and whether they had documents in place.",
     "I'm sorry — these calls come at one of the hardest moments. EPLLC handles probate and trust administration with experienced attorneys (Charles personally, often Nicholas for complex matters). The firm uses a proprietary EPLLC Client Portal and iOS app to give families secure document access during what's already a chaotic time. The two things that help the team move quickly: who passed, and whether they had documents in place."),
    # Elder/Medicaid path
    ("Elder law calls usually surface at one of three moments: parent's care needs escalating, a Medicaid eligibility question just got real, or a Veteran is being denied aid &amp; attendance benefits. Murphy &amp; Berglund is VA-accredited (rare for an estate firm) and handles all three — long-term care planning, Medicaid spend-down, asset protection trusts, VA benefits applications, guardianship.",
     "Elder law calls usually surface at two specific events: a parent's care needs are escalating, or a Medicaid eligibility question just got real (often when an asset transfer's already happened or a nursing home admission is days away). EPLLC's Medicaid Crisis Planning practice exists for exactly that scenario — when the standard 5-year lookback rules already apply and the family needs immediate intervention."),
    # Wills/trusts path
    ("Smart to think about this before you need it. Michelle handles wills, trusts, powers of attorney, and healthcare surrogates as a coordinated package — and notably, she's one of the few estate attorneys in Central FL with a Cryptocurrency Law practice, which matters more every year as people hold digital assets without thinking about how they pass.",
     "Smart to think about this before you need it. EPLLC's planning practice covers wills, trusts, powers of attorney, healthcare surrogates, AND specialty trusts most firms don't handle — Gun Trusts (NFA-compliant trusts for firearms), Special Needs Planning (for disabled beneficiaries), and Asset Protection Planning. The firm's iOS app lets you access documents from anywhere once they're done."),
    # Booking
    ("'estate': 'Probate / Trust Admin Consultation',\n          'planning': 'Estate Planning + Crypto Asset Consult',\n          'elder': 'Elder Law / Medicaid / VA Benefits Consult',\n          'question': 'General Consultation'",
     "'estate': 'Probate / Trust Admin Consultation',\n          'planning': 'Estate Planning Consult (Wills / Trusts / Gun Trusts / SN)',\n          'elder': 'Elder Law / Medicaid Crisis Consult',\n          'question': 'General Consultation'"),
    ('<div class="booking-icon">M</div>', '<div class="booking-icon">E</div>'),
    ('<span class="value">Michelle Berglund-Harper or Jodi Murphy, Esq.</span>',
     '<span class="value">Charles Wilder · Melissa Moses Parker · Nicholas Rubino, Esq.</span>'),
    ('<span class="value">1101 Douglas Ave, Altamonte Springs</span>',
     '<span class="value">711 Ballard Street, Altamonte Springs</span>'),
    ("Michelle and Jodi", "the EPLLC team"),
    ("Jodi", "Charles or Nicholas"),
    ("Michelle", "Charles or Melissa"),
]
EPLLC_CLEANUP = [
    ("Murphy &amp; Berglund", "EPLLC"),
    ("Murphy & Berglund", "EPLLC"),
    ("murphyberglund.com", "epllc-plc.com"),
]

# ---- BÁNH MÌ BOY — Vietnamese, Mills 50 (base: pigfloyds.html) ----
# Real data: Chef Hung Huynh (Top Chef WINNER!), since 1988 (37+ years), Michelin Bib
# Gourmand 2025, Netflix Somebody Feed Phil S7, pho French dip banh mi, fresh bread daily,
# Vietnamese coffee + sugarcane juice, 1110 East Colonial Drive (inside Mills Market)
BANHMI_SUBS = [
    ("Pig Floyd's Urban Barbakoa — Reservations & Catering Concierge | Powered by Velo AI",
     "Bánh Mì Boy — Reservations Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Pig Floyd's Urban Barbakoa.",
     "This is a live demo built by Velo AI for Bánh Mì Boy"),
    ("Mills 50, Orlando · Slow-Smoked",
     "Mills 50 · Michelin Bib Gourmand · Top Chef"),
    ("<h1 class=\"practice-name\">Pig Floyd's Urban Barbakoa</h1>",
     '<h1 class="practice-name">Bánh Mì Boy</h1>'),
    ('<p class="practice-doctor">Thomas, Owner</p>',
     '<p class="practice-doctor">Chef Hung Huynh · Top Chef Winner</p>'),
    ("Pig Floyd's runs hot during dinner service and the team can't always pause to answer calls — but reservations, takeout, and catering inquiries get captured around the clock.",
     "Bánh Mì Boy has been part of Mills 50 since 1988. With Top Chef winner Hung Huynh leading the kitchen, Michelin Bib Gourmand recognition (2025), and a Netflix &quot;Somebody Feed Phil&quot; feature (Season 7), the calls and texts that hit the line aren't just neighborhood — they're national. The team can't pause to answer the phone mid-service. The concierge captures reservations, catering inquiries, and questions any time of day."),
    ("1326 N Mills Ave<br>Orlando, FL 32803",
     "1110 East Colonial Drive<br>Orlando, FL 32803"),
    ("(407) 203-0866", "(407) 422-0067"),
    ("Tue–Sun · Lunch & Dinner Service",
     "Mon–Thu 10:30a–9p · Fri–Sun 10a–9:30p"),
    ("<strong>Pig Floyd's Concierge</strong> · Available 24/7",
     "<strong>Bánh Mì Boy Concierge</strong> · Available 24/7"),
    ("Catering or large party? Thomas will be notified directly for time-sensitive bookings.",
     "Catering, media inquiry, or large party? Chef Hung's team is notified directly."),
    ("Welcome to Pig Floyd's. The dining room is loud and the smokers are working — the team can't always pick up. I'm the after-hours line: I can take reservations, quote catering, and answer most menu questions before service tomorrow.",
     "Welcome to Bánh Mì Boy. We've been part of Mills 50 since 1988. The kitchen runs hot — fresh bread baked daily in-house, house-made pâté, Vietnamese coffee and sugarcane juice — so the team can't always pause for the phone. I'm the after-hours line: I can take large-party reservations, quote catering, walk you through the menu (including the pho French dip bánh mì or build-your-own summer rolls), and route media or partnership inquiries to the team."),
    ("// CATERING PATH ----------\n    if (value === 'high-value') {\n      memory.concern = 'catering';\n      await addBotMessage(\n        `Catering is one of Pig Floyd's strengths — the smoker doesn't sleep, so we can scale up for almost any event. What kind of event?`,",
     "// CATERING PATH ----------\n    if (value === 'high-value') {\n      memory.concern = 'catering';\n      await addBotMessage(\n        `Bánh Mì Boy catering is its own thing — the bread is baked fresh daily so we plan ahead with the kitchen. What kind of event?`,"),
    ("'implants': 'corporate catering',\n      'invisalign': 'wedding catering',\n      'both': 'family-style catering'",
     "'implants': 'office or corporate catering',\n      'invisalign': 'event catering',\n      'both': 'large-party platter (Saigon street style)'"),
    ("Pig Floyd's catering ranges from BBQ trays for 10 people up to full-service events for 200+. Pricing usually lands $18-32 per person depending on protein mix and service style. Thomas does a free 15-minute call to scope events before quoting — that way the quote is real, not generic.",
     "Bánh Mì Boy catering ranges from bánh mì platters for 10 people up to full Vietnamese spreads for 100+ (pho stations, summer roll bars, Saigon street wings). Pricing usually lands $14-22 per person depending on the menu mix. The team does a quick scoping call before quoting so the quote actually fits your event."),
    ("'implants': 'Corporate Catering Consult',\n          'invisalign': 'Event Catering Consult',\n          'both': 'Family Catering Consult',\n          'emergency': 'Reservation'",
     "'implants': 'Office Catering Consult',\n          'invisalign': 'Event Catering Consult',\n          'both': 'Large-Party Saigon Street Consult',\n          'emergency': 'Reservation'"),
    ("Pickup orders go through our online system — fastest way is to order at pigfloyds.com/order or call (407) 203-0866 during service. If you want me to text you the link or hold a name in the system for tomorrow, what's your first name?",
     "Pickup orders are easiest by calling (407) 422-0067 during service or ordering through the website. If you want me to text the menu link to your phone or hold a name in the system for tomorrow, what's your first name?"),
    ("Of course — type your question. Hours, menu items, dietary stuff (we have vegan smoke options), or anything specific to a dish — I can usually answer right now.",
     "Of course — type your question. Hours, the menu (bánh mì varieties, pho, summer rolls, Saigon street wings, sugarcane juice, Vietnamese coffee), dietary stuff (we have vegetarian and tofu options), or media/partnership inquiries — I can usually answer right now."),
    ('<div class="booking-icon">P</div>', '<div class="booking-icon">B</div>'),
    ("<span class=\"value\">Pig Floyd's Team</span>",
     '<span class="value">Bánh Mì Boy Team</span>'),
    ('<span class="value">1326 N Mills Ave, Orlando</span>',
     '<span class="value">1110 East Colonial Drive (Mills Market)</span>'),
    ("(407) 203-0866", "(407) 422-0067"),
    ("Pig Floyd's", "Bánh Mì Boy"),
    ("Thomas", "Chef Hung"),
    ("the smoker doesn't sleep", "the bread is baked fresh daily"),
    ("see you at the smoker", "see you at the cafe"),
]
BANHMI_CLEANUP = [
    ("pigfloyds.com", "banhmiboycafe.com"),
]

# ---- GIOVANNI'S PIZZERIA — Italian family, Lake Mary (base: adriatico.html) ----
# Real data: Family-owned, Central Italian, Calabrian Honey wings, signature cocktails
# (Amalfi Coast, Calabrón, Soprano, Espress Yourself), 5 locations, complimentary bread,
# 24-hour wing marinade
GIOVANNIS_SUBS = [
    ("Adriatico Trattoria Italiana — Reservations Concierge | Powered by Velo AI",
     "Giovanni's Pizzeria &amp; Kitchen — Reservations Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Adriatico Trattoria Italiana",
     "This is a live demo built by Velo AI for Giovanni's Pizzeria &amp; Kitchen"),
    ("College Park, Orlando · Old-World Italian",
     "Lake Mary · 5 Locations · Family-Owned"),
    ('<h1 class="practice-name">Adriatico Trattoria</h1>',
     "<h1 class=\"practice-name\">Giovanni's Pizzeria</h1>"),
    ('<p class="practice-doctor">Chef Marco &amp; Rosetta Cudazzo</p>',
     '<p class="practice-doctor">Family-Owned · Central Italian Tradition</p>'),
    ("Adriatico is a true trattoria — Marco at the pass running fresh pasta, Rosetta in the dining room making sure every guest is taken care of. The phone gets in the way of both jobs. The concierge captures reservations, dietary planning, and private events around the clock.",
     "Giovanni's runs five Central Florida locations — Lake Mary, Davenport, Lake Nona (two), Oviedo. Each one needs to handle reservations, takeout orders, catering inquiries, and large-party bookings during dinner rush. The team can't pause service to answer the phone. The concierge captures it all and routes by location."),
    ("2417 Edgewater Drive<br>Orlando, FL 32804",
     "Lake Mary · Davenport · Lake Nona · Oviedo<br>5 Florida Locations"),
    ("(407) 428-0044", "(407) 330-4350"),
    ("Mon–Sat 5p · Last Seating 8:30p",
     "Lunch &amp; Dinner Daily · 5 Locations"),
    ("<strong>Adriatico Concierge</strong> · Available 24/7",
     "<strong>Giovanni's Concierge</strong> · Available 24/7"),
    ("Special occasion or private dinner? Marco and Rosetta will be notified directly.",
     "Special occasion, large party, or catering? The right location's team will be notified directly."),
    ("Welcome to Adriatico. Marco's at the pass — fresh pasta is made-to-order, so he can't step away mid-service to take the phone. Rosetta's running the room. I'm here in their place: I can take reservations, walk through the menu and any dietary considerations, scope private events, and have anything time-sensitive in front of them before tomorrow's dinner service.",
     "Welcome to Giovanni's. Five Florida locations — Lake Mary, Davenport, two in Lake Nona, and Oviedo — all running dinner service simultaneously. The team can't always pause to answer. I'm here to take reservations, route by location, walk you through the menu (Central Italian, hand-tossed pizza, signature cocktails like Amalfi Coast and Calabrón), scope catering, and handle large-party bookings."),
    ("Private events at Adriatico are intimate by nature — the trattoria is meant for tables of friends, not banquet rooms. Most private events are 8-20 guests with a curated multi-course Italian dinner Marco builds for the occasion. What kind of event are you considering?",
     "Giovanni's hosts private events and large parties regularly across all five locations — birthdays, corporate dinners, retirement parties, sports celebrations. Each location can accommodate different sizes (Lake Mary and Lake Nona Town Center handle 40+, Davenport and Oviedo work better at 15-30). What kind of event are you considering?"),
    ("Private events at Adriatico start at 8 guests with a four-to-six course Italian progression. Pricing typically lands $75-125 per person depending on the menu and wine pairings. Marco does a planning call before quoting so the menu actually reflects what you and your guests will love (and what's freshest that week).",
     "Giovanni's events start with a planning call to understand the size, the location that fits, and the menu mix (pizza station, family-style pasta, full multi-course). Pricing typically runs $25-55 per person depending on what's served and which location. The team does the quote after they understand the event."),
    ("Adriatico's menu features hand-made fresh pasta and old-world Italian cooking inspired by the Adriatic coast. I can walk through the regions represented, the wine program (Italy-focused), dietary accommodations Marco can prepare with notice, or specific dishes. What would help?",
     "Giovanni's menu is Central Italian — hand-tossed pizzas (Margherita, Giovanni's Primo, The Don), pastas (Rigatoni alla Roma, Pasta Bella, Lasagna, Fettuccine Alfredo), the famous Calabrian Honey wings (24-hour marinade), and signature cocktails (Amalfi Coast, Calabrón, Soprano, Espress Yourself). Complimentary house-baked bread comes with every table. What can I help with?"),
    ("(407) 428-0044", "(407) 330-4350"),
    ('<div class="booking-icon">A</div>', '<div class="booking-icon">G</div>'),
    ('<span class="value">Marco &amp; Rosetta</span>',
     "<span class=\"value\">Giovanni's Team</span>"),
    ('<span class="value">2417 Edgewater Drive, Orlando</span>',
     '<span class="value">Lake Mary · Davenport · Lake Nona · Oviedo</span>'),
    ("Marco", "Giovanni's chef team"),
    ("Adriatico", "Giovanni's"),
]
GIOVANNIS_CLEANUP = [
    ("adriatico-trattoria.com", "giovannisrestaurant.com"),
]

# ---- STUDIO 312 SALON — Oviedo full-service (base: thelook.html) ----
# Real data: Rachel (owner) + 11 stylists named, 4 Brazilian Blowout options,
# K-18 / L'Oreal / Matrix / Mizani / Redken / Brazilian Blowout, curly hair specialty,
# education-focused, 1755 W Broadway St Oviedo
STUDIO312_SUBS = [
    ("The Look Salon &amp; Spa — Booking Concierge | Powered by Velo AI",
     "Studio 312 Salon — Booking Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for The Look Salon & Spa.",
     "This is a live demo built by Velo AI for Studio 312 Salon"),
    ("Oviedo, Florida · Hair, Spa &amp; Skincare",
     "Oviedo, Florida · Owner-Operated · 12 Stylists"),
    ('<h1 class="practice-name">The Look Salon &amp; Spa</h1>',
     '<h1 class="practice-name">Studio 312 Salon</h1>'),
    ('<p class="practice-doctor">17 Stylists · Award-Winning Team</p>',
     '<p class="practice-doctor">Owner Rachel · 12-Stylist Team</p>'),
    ("Seventeen stylists, 90+ services, and 4.9 stars across 1,100+ Google reviews. The Look handles hair (Hattori Hanzo trained, REZO Certified for curls), spa, skincare, and lashes (NovaLash certified) under one roof. The booking line never sleeps.",
     "Studio 312 is owner-operated by Rachel with 11 additional stylists. Specialties include curly cuts, four different Brazilian Blowout options, K-18, and color work across L'Oréal, Matrix, Mizani, and Redken lines. The salon's positioning is education-focused: clients leave knowing how to maintain their look at home."),
    ("3635 Aloma Ave, Suite 1025<br>Oviedo, FL 32765",
     "1755 W Broadway Street, Suite 3<br>Oviedo, FL 32765"),
    ("Mon-Sat · See Hours", "Daily 8a-9p · By Stylist Schedule"),
    ("<strong>The Look Concierge</strong> · Available 24/7",
     "<strong>Studio 312 Concierge</strong> · Available 24/7"),
    ("A regular at The Look? Your stylist will be notified directly for time-sensitive bookings.",
     "A regular at Studio 312? Your stylist (Rachel, Emerald, Rini, Brittany, Josie, Melinda, Peyton, Brooke, Nikia, Liberty, Soledad, or Marli) will be notified directly."),
    ("Welcome to The Look. The salon is wrapped for the night, but I can hold appointments across all 17 stylists, quote services (we do 90+, from precision Hattori Hanzo cuts to REZO Certified curl work to NovaLash extensions), and answer most questions before you go to sleep.",
     "Welcome to Studio 312. The salon is wrapped for the night, but I can hold appointments with Rachel or any of the 11 stylists, quote services (cuts, all-over color, gray coverage, balayage, blonding, curly cuts, four Brazilian Blowout options, K-18 treatments, makeup, waxing), and answer questions about products and home care before you go to sleep."),
    # Curl path is still relevant — Studio 312 also does curly
    ("Curls are a specialty — Solice Del Mazo is REZO Certified and books out fastest. The other curl-friendly stylists at The Look are also trained on the dry-cutting REZO method, so we can get you in either way.<br><br>Can I get your first name and best phone number? I'll have Solice or her team confirm in the morning.",
     "Curly cuts are a specialty at Studio 312 — the team is trained to cut curls dry rather than wet, which makes a real difference for textured hair. Several stylists handle curls so you have options.<br><br>Can I get your first name and best phone number? I'll have a curl-specialist stylist confirm in the morning."),
    ("Color and extensions are core specialties at The Look — the salon partners with Wella, Brazilian Blowout, Moroccan Oil, and Redken, so most modern color work is in-house. Tuesday or Thursday have the most flexibility for new color clients.<br><br>What's your first name? I'll have someone pre-confirm with you by tomorrow morning.",
     "Color is a core focus at Studio 312 — the team works across L'Oréal, Matrix, Mizani, and Redken color lines for different needs (gray coverage, balayage, blonding all use different products and techniques). Tuesday or Thursday have the most flexibility for new color clients.<br><br>What's your first name? I'll have someone pre-confirm with you by tomorrow morning."),
    # Spa path → Studio 312 has makeup + waxing (no spa)
    ("The Look's spa side handles facials (rejuvenating, anti-wrinkle), microblading, eyebrow tinting, full body waxing, and skincare consultations. The estheticians do continuing education quarterly so the techniques stay current. What's your first name? I'll have the right specialist follow up tomorrow morning.",
     "Studio 312's deep-conditioning, K-18, keratin, and Brazilian Blowout treatments are popular for clients dealing with damage or wanting to extend a smooth blowout. The salon also does makeup application (great for events) and waxing. What's your first name? I'll have the right stylist follow up tomorrow morning."),
    ('<div class="booking-icon">L</div>', '<div class="booking-icon">3</div>'),
    ('<span class="value">The Look Stylist</span>',
     '<span class="value">Studio 312 Stylist</span>'),
    ('<span class="value">151 Geneva Dr, Oviedo</span>',
     '<span class="value">1755 W Broadway St, Oviedo</span>'),
    ("(407) 977-8481", "(321) 318-6296"),
    ("The Look", "Studio 312"),
]
STUDIO312_CLEANUP = []

# ---- ELITE DENTISTRY — Avalon Park, Orlando (base: wayside.html) ----
# Real data: Dr. Mark Ashy (owner, FL native, father, family-oriented), America's Best
# Dentists by National Consumer Advisory Board, 13000 Avalon Lake Drive Suite 201,
# (407) 658-0103
ELITEDENTAL_SUBS = [
    ("Wayside Family Dental — After-Hours Concierge | Powered by Velo AI",
     "Elite Dentistry — After-Hours Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Wayside Family Dental.",
     "This is a live demo built by Velo AI for Elite Dentistry"),
    ("Sanford, Florida · Est. 2012",
     "Avalon Park, Orlando · Family-Oriented"),
    ('<h1 class="practice-name">Wayside Family Dental</h1>',
     '<h1 class="practice-name">Elite Dentistry</h1>'),
    ('<p class="practice-doctor">Dr. Lyudmila A. Onyski, DDS</p>',
     '<p class="practice-doctor">Dr. Mark Ashy · Owner</p>'),
    ("Dr. Onyski is on call to respond to her patients' needs as soon as possible. As a patient of Wayside, you're never alone.",
     "Dr. Mark Ashy — a Florida native and father — runs Elite Dentistry as the kind of family practice where the entire household can come to one office. He's on call for patient needs after hours. You're never alone."),
    ("4907 International Pkwy, Suite 1041<br>Sanford, FL 32771",
     "13000 Avalon Lake Drive, Suite 201<br>Orlando, FL 32828"),
    ("<div>(407) 732-4570</div>", "<div>(407) 658-0103</div>"),
    ("Mon–Thu 8a–5p · Fri 8a–1p",
     "Mon–Thu 8:30a–5p · Fri 8:30a–4p"),
    ("<strong>Wayside Concierge</strong> · Available 24/7",
     "<strong>Elite Dentistry Concierge</strong> · Available 24/7"),
    ("A patient of Wayside? Dr. Onyski will be notified immediately for urgent matters.",
     "A patient of Elite Dentistry? Dr. Ashy will be notified immediately for urgent matters."),
    ("Good evening — you've reached the after-hours line for Wayside Family Dental. Dr. Onyski is unavailable right now, but I can help with most things and reach her directly if it's urgent.",
     "Good evening — you've reached the after-hours line for Elite Dentistry in Avalon Park. Dr. Mark Ashy has been recognized as one of America's Best Dentists by the National Consumer Advisory Board, and runs the practice as the family dentist for Avalon Park, Stoneybrook, Eastwood, and surrounding areas. He's wrapped for the day, but I can help with most things and reach him directly if it's urgent."),
    ("Dr. Onyski has been doing both since 2010, so you're in capable hands.",
     "Elite Dentistry has been performing both for years — Dr. Ashy handles general, cosmetic, restorative, and pediatric dentistry under one roof, plus implant restorations and emergency care. You're in capable hands."),
    ("Dr. Onyski has been welcoming new patients to Wayside since 2012",
     "Elite Dentistry has been welcoming new families to Avalon Park"),
    ("texting Dr. Onyski now — she'll call you back",
     "texting Dr. Ashy now — he'll call you back"),
    ("Dr. Onyski will want to see you first thing — she keeps emergency slots",
     "Dr. Ashy will want to see you first thing — he keeps same-day or next-day emergency slots"),
    ("Dr. Onyski's office", "the office"),
    ("Dr. Onyski has been notified", "Dr. Ashy has been notified"),
    ("Dr. Onyski opens new-patient slots", "Dr. Ashy opens new-patient slots"),
    ("Dr. Onyski has openings", "Dr. Ashy has openings"),
    ("Dr. Onyski needs to weigh in", "Dr. Ashy needs to weigh in"),
    ("she'll call", "he'll call"),
    ("she keeps emergency slots", "he keeps emergency slots"),
    ("she calls", "he calls"),
    ('<div class="booking-icon">W</div>', '<div class="booking-icon">E</div>'),
    ('<span class="value">Dr. Lyudmila A. Onyski</span>',
     '<span class="value">Dr. Mark Ashy</span>'),
    ('<span class="value">4907 International Pkwy, Suite 1041</span>',
     '<span class="value">13000 Avalon Lake Drive, Orlando</span>'),
    ("(407) 732-4570", "(407) 658-0103"),
    ("Dr. Onyski", "Dr. Ashy"),
    ("Wayside", "Elite Dentistry"),
]
ELITEDENTAL_CLEANUP = [
    ("Wayside", "Elite Dentistry"),
    ("Onyski", "Ashy"),
]

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


# ---- ROUND 5 — net-new prospects ----

# Root & Branch Bistro and Bar (Clermont) — Jason & Casey Baruch (proprietors), Chef David M Henry
# Best of South Lake, OpenTable Diner's Choice, 4.7 stars / 1,480 reviews
# Closed Mon-Tues; Wed/Thu/Sun 3-9pm; Fri/Sat 3-10pm
# Voice: "dressing up is optional" — upscale-yet-unpretentious bistro
ROOTBRANCH_SUBS = [
    ("Pig Floyd's Urban Barbakoa — Reservations & Catering Concierge | Powered by Velo AI",
     "Root & Branch Bistro and Bar — Reservations & Private Events Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Pig Floyd's Urban Barbakoa.",
     "This is a live demo built by Velo AI for Root & Branch Bistro and Bar."),
    ('<h1 class="practice-name">Pig Floyd\'s Urban Barbakoa</h1>',
     '<h1 class="practice-name">Root & Branch Bistro and Bar</h1>'),
    ("Pig Floyd's runs hot during dinner service and the team can't always pause to answer calls — but reservations, takeout, and catering inquiries get captured around the clock.",
     "Root & Branch is dinner-only Wednesday through Sunday — when the kitchen's deep in service, reservation calls and private-event questions get missed. This line catches them around the clock."),
    ("<strong>Pig Floyd's Concierge</strong> · Available 24/7",
     "<strong>Root &amp; Branch Concierge</strong> · Available 24/7"),
    ("Pig Floyd's Concierge",
     "Root & Branch Concierge"),
    ('<span class="value">Pig Floyd\'s Team</span>',
     '<span class="value">Jason &amp; Casey Baruch · Chef David M Henry</span>'),
    ("Welcome to Pig Floyd's. The dining room is loud and the smokers are working — the team can't always pick up. I'm the after-hours line: I can take reservations, quote catering, and answer most menu questions before service tomorrow.<br><br>What brings you here tonight?",
     "Welcome to Root & Branch. The kitchen's running and the front-of-house can't always pick up — I'm the after-hours line. I can take reservations, scope private events, and answer most menu questions before tomorrow's service.<br><br>What brings you here tonight?"),
    ("Catering is one of Pig Floyd's strengths — the smoker doesn't sleep, so we can scale up for almost any event. What kind of event?",
     "Private events are one of the things Root & Branch does best — Chef Henry has built tasting menus for everything from rehearsal dinners to corporate offsites. What kind of event?"),
    ("Most clients asking about ${txt} are wondering: <em>\"How many people can you feed?\"</em> and <em>\"What's it going to cost?\"</em><br><br>Pig Floyd's catering ranges from BBQ trays for 10 people up to full-service events for 200+. Pricing usually lands $18-32 per person depending on protein mix and service style. Thomas does a free 15-minute call to scope events before quoting — that way the quote is real, not generic.<br><br>Want me to hold a slot this week?",
     "Most folks asking about ${txt} want to know: <em>\"What's the format?\"</em> and <em>\"What's it going to run per person?\"</em><br><br>Root & Branch handles parties from 12 (chef's table) up through full buyouts of the dining room. Tasting menus typically land $55-85 per person depending on courses and wine pairing. Jason does a quick scoping call before quoting — that way the number is real, not generic.<br><br>Want me to hold a slot this week?"),
    ("Pickup orders go through our online system — fastest way is to order at pigfloyds.com/order or call (407) 203-0866 during service.",
     "Reservations go through OpenTable — fastest way is to book at rootandbranchbistroandbar.com or call (352) 708-4529 during service."),
    ("Perfect. Here's the hold I'm creating for the Pig Floyd's team:",
     "Perfect. Here's the hold I'm creating for the Root & Branch team:"),
    ("No problem. Pig Floyd's has tables available Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM — which works best?",
     "No problem. Root & Branch has tables Wednesday at 6 PM, Friday at 7:30 PM, or Sunday at 5 PM — which works best?"),
    ("Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM",
     "Wednesday at 6 PM, Friday at 7:30 PM, or Sunday at 5 PM"),
    ("(407) 203-0866", "(352) 708-4529"),
    ("Thomas", "Jason"),
    ("Pig Floyd", "Root &amp; Branch"),
]
ROOTBRANCH_CLEANUP = [
    ("Pig Floyd", "Root & Branch"),
    ("pigfloyds", "rootandbranch"),
]


# Infinity Dental (Apopka) — Dr. Sushil Patel, Beef O'Brady's Plaza
# 1450 N Rock Springs Rd, Apopka, FL 32712 — (407) 814-4940
# Patient praise: "didn't push unnecessary procedures" — perfect for honest-care register
# Services: general, cosmetic, Invisalign, implants, root canals, same-day emergencies
INFINITY_SUBS = [
    ("Wayside Family Dental — After-Hours Concierge | Powered by Velo AI",
     "Infinity Dental — After-Hours Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Wayside Family Dental.",
     "This is a live demo built by Velo AI for Infinity Dental."),
    ("Sanford, Florida · Est. 2012", "Apopka, Florida · Skilled, Modern, Compassionate"),
    ('<h1 class="practice-name">Wayside Family Dental</h1>',
     '<h1 class="practice-name">Infinity Dental</h1>'),
    ('<p class="practice-doctor">Dr. Lyudmila A. Onyski, DDS</p>',
     '<p class="practice-doctor">Dr. Sushil Patel, DDS</p>'),
    ("Dr. Onyski is on call to respond to her patients' needs as soon as possible. As a patient of Wayside, you're never alone.",
     "Dr. Patel is committed to responding to patient needs as quickly as possible. As a patient of Infinity, you're never alone — and you'll never be pushed into treatment you don't need."),
    ("4907 International Pkwy, Suite 1041<br>Sanford, FL 32771",
     "1450 N Rock Springs Rd<br>Apopka, FL 32712"),
    ("(407) 732-4570", "(407) 814-4940"),
    ("<strong>Wayside Concierge</strong> · Available 24/7",
     "<strong>Infinity Dental Concierge</strong> · Available 24/7"),
    ("A patient of Wayside? Dr. Onyski will be notified immediately for urgent matters.",
     "A patient of Infinity? Dr. Patel will be notified immediately for urgent matters."),
    ("Good evening — you've reached the after-hours line for Wayside Family Dental. Dr. Onyski is unavailable right now, but I can help with most things and reach her directly if it's urgent.",
     "Good evening — you've reached the after-hours line for Infinity Dental. Dr. Patel is unavailable right now, but I can help with most things and reach him directly if it's urgent."),
    ("I'm sorry you're dealing with this — dental pain at this hour is genuinely awful, and you did the right thing reaching out. Let me get you to Dr. Onyski as quickly as possible.",
     "I'm sorry you're dealing with this — dental pain at this hour is genuinely awful, and you did the right thing reaching out. Let me get you to Dr. Patel as quickly as possible."),
    ("Understood. I'm flagging this as urgent and texting Dr. Onyski now — she'll call you back within 15 minutes.",
     "Understood. I'm flagging this as urgent and texting Dr. Patel now — he'll call you back within 15 minutes."),
    ("Got it. Dr. Onyski will want to see you first thing — she keeps emergency slots open every morning at 8 AM specifically for situations like this.",
     "Got it. Dr. Patel will want to see you first thing — he keeps same-day emergency slots open specifically for situations like this."),
    ("Great choice to reach out — both implants and Invisalign are major decisions and Dr. Onyski has been doing both since 2010, so you're in capable hands.",
     "Great choice to reach out — both implants and Invisalign are major decisions, and Dr. Patel has built his practice around honest treatment planning. You'll get a clear answer on whether you're a candidate before anyone talks dollars."),
    ("Most patients asking about ${txt} have one of two questions on their mind: <em>\"Am I a candidate?\"</em> and <em>\"What will it actually cost?\"</em><br><br>Both are best answered with a 30-minute consult — Dr. Onyski does a digital scan, reviews your options, and gives you a treatment plan with real numbers before you commit to anything. Wayside also accepts CareCredit if financing helps.",
     "Most patients asking about ${txt} have one of two questions: <em>\"Am I a candidate?\"</em> and <em>\"What will it actually cost?\"</em><br><br>Dr. Patel handles both in a single consult — digital scan, real options, and a treatment plan with actual numbers before you commit. Patients often comment that he doesn't push procedures you don't need. CareCredit available if financing helps."),
    ("Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Dr. Onyski's schedule?",
     "Perfect. Let me hold ${timeMap[value]} for you. What's your first name so I can put it on Dr. Patel's schedule?"),
    ("Welcome — Dr. Onyski has been welcoming new patients to Wayside since 2012, and most of our patients come from referrals, so it's nice when someone finds us directly.",
     "Welcome — Dr. Patel built Infinity Dental around skilled, modern, compassionate care. A lot of patients come from referrals, so it's nice when someone finds us directly."),
    ("Of course — go ahead and type your question and I'll do my best. If it's something Dr. Onyski needs to weigh in on personally, I'll route it to her and she'll get back to you in the morning.",
     "Of course — go ahead and type your question and I'll do my best. If it's something Dr. Patel needs to weigh in on personally, I'll route it to him and he'll get back to you in the morning."),
    ("Thank you, ${memory.name}. What's the best phone number to reach you at? I want to make sure Dr. Onyski has it before tomorrow morning.",
     "Thank you, ${memory.name}. What's the best phone number to reach you at? I want to make sure Dr. Patel has it before tomorrow morning."),
    ("Thanks, ${memory.name}. What's the best phone number? Dr. Onyski's office will text you a confirmation within an hour of opening.",
     "Thanks, ${memory.name}. What's the best phone number? Dr. Patel's office will text you a confirmation within an hour of opening."),
    ("Thank you, ${memory.name}. What's the best callback number? Dr. Onyski will call you within 15 minutes.",
     "Thank you, ${memory.name}. What's the best callback number? Dr. Patel will call you within 15 minutes."),
    ("Perfect. Here's the hold I'm creating for Dr. Onyski:",
     "Perfect. Here's the hold I'm creating for Dr. Patel:"),
    ("Got it, ${memory.name} — I just paged Dr. Onyski. Expect a call from <strong>(407) 732-4570</strong> within 15 minutes.<br><br>Stay calm, sit upright if possible, and avoid hot or cold liquids until she calls. You're going to be okay.",
     "Got it, ${memory.name} — I just paged Dr. Patel. Expect a call from <strong>(407) 814-4940</strong> within 15 minutes.<br><br>Stay calm, sit upright if possible, and avoid hot or cold liquids until he calls. You're going to be okay."),
    ("All set, ${memory.name}. Dr. Onyski's office will call (${text}) by 7:30 AM to confirm your appointment.",
     "All set, ${memory.name}. Dr. Patel's office will call (${text}) by 8:30 AM to confirm your appointment."),
    ("Got it. Dr. Onyski opens new-patient slots Tuesday through Thursday — would tomorrow at 10:30 AM or Wednesday at 2 PM work better for you?",
     "Got it. Dr. Patel opens new-patient slots Monday through Friday — would tomorrow at 10:30 AM or Wednesday at 2 PM work better for you?"),
    ("Thanks for sending that over. I've logged your question for Dr. Onyski to review first thing in the morning — she or someone from her team will reach out by 10 AM.",
     "Thanks for sending that over. I've logged your question for Dr. Patel to review first thing in the morning — he or someone from his team will reach out by 10 AM."),
    ("You're all set, ${memory.name}. Dr. Onyski has been notified, and you'll get a confirmation text from <strong>(407) 732-4570</strong> within the hour.<br><br>Have a good night — and thank you for choosing Wayside.",
     "You're all set, ${memory.name}. Dr. Patel has been notified, and you'll get a confirmation text from <strong>(407) 814-4940</strong> within the hour.<br><br>Have a good night — and thank you for choosing Infinity Dental."),
    ('<span class="value">Dr. Lyudmila A. Onyski</span>',
     '<span class="value">Dr. Sushil Patel</span>'),
    ('<span class="value">4907 International Pkwy, Suite 1041</span>',
     '<span class="value">1450 N Rock Springs Rd, Apopka</span>'),
    ('<div class="booking-icon">W</div>', '<div class="booking-icon">I</div>'),
    ("Dr. Onyski", "Dr. Patel"),
    ("Onyski", "Patel"),
    ("Wayside", "Infinity Dental"),
    ("she'll", "he'll"),
    ("she keeps", "he keeps"),
    ("she calls", "he calls"),
    ("she's", "he's"),
    ("she ", "he "),
    ("her ", "his "),
]
INFINITY_CLEANUP = [
    ("Wayside", "Infinity Dental"),
    ("Onyski", "Patel"),
]


# The Classic Thornton Park — Orlando gastropub, smash burgers + thick milkshakes, brunch on weekends
# Address area: 805 E Washington St (Thornton Park) — voice: warm, comfort-food, "Food to warm your bellies"
CLASSICTP_SUBS = [
    ("Pig Floyd's Urban Barbakoa — Reservations & Catering Concierge | Powered by Velo AI",
     "The Classic Thornton Park — Reservations & Catering Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Pig Floyd's Urban Barbakoa.",
     "This is a live demo built by Velo AI for The Classic Thornton Park."),
    ('<h1 class="practice-name">Pig Floyd\'s Urban Barbakoa</h1>',
     '<h1 class="practice-name">The Classic Thornton Park</h1>'),
    ("Pig Floyd's runs hot during dinner service and the team can't always pause to answer calls — but reservations, takeout, and catering inquiries get captured around the clock.",
     "The Classic runs late on Thornton Park's busiest nights and brunch crowds back up the line on weekends. Reservation calls, catering questions, and takeout inquiries get captured around the clock so the team can focus on the floor."),
    ("<strong>Pig Floyd's Concierge</strong> · Available 24/7",
     "<strong>The Classic Concierge</strong> · Available 24/7"),
    ("Pig Floyd's Concierge", "The Classic Concierge"),
    ('<span class="value">Pig Floyd\'s Team</span>',
     '<span class="value">The Classic Thornton Park Team</span>'),
    ("Welcome to Pig Floyd's. The dining room is loud and the smokers are working — the team can't always pick up. I'm the after-hours line: I can take reservations, quote catering, and answer most menu questions before service tomorrow.<br><br>What brings you here tonight?",
     "Welcome to The Classic Thornton Park. The dining room's running and the team can't always pick up — I'm the after-hours line. I can take reservations, scope catering for special occasions, and answer most menu questions before tomorrow's service.<br><br>What brings you here tonight?"),
    ("Catering is one of Pig Floyd's strengths — the smoker doesn't sleep, so we can scale up for almost any event. What kind of event?",
     "Catering is one of The Classic's strengths — the kitchen scales for everything from office lunches to private celebrations. What kind of event?"),
    ("Most clients asking about ${txt} are wondering: <em>\"How many people can you feed?\"</em> and <em>\"What's it going to cost?\"</em><br><br>Pig Floyd's catering ranges from BBQ trays for 10 people up to full-service events for 200+. Pricing usually lands $18-32 per person depending on protein mix and service style. Thomas does a free 15-minute call to scope events before quoting — that way the quote is real, not generic.<br><br>Want me to hold a slot this week?",
     "Most folks asking about ${txt} want to know: <em>\"What's the format?\"</em> and <em>\"What's it going to cost per person?\"</em><br><br>The Classic handles parties from 10 (private brunch) up through full buyouts of the dining room. Catering platters and event packages typically land $22-45 per person depending on selections. The team does a quick scoping call before quoting — that way the number is real.<br><br>Want me to hold a slot this week?"),
    ("Pickup orders go through our online system — fastest way is to order at pigfloyds.com/order or call (407) 203-0866 during service.",
     "Takeout orders are easiest by phone — call (407) 730-5646 during service or grab a table on OpenTable for dine-in."),
    ("Perfect. Here's the hold I'm creating for the Pig Floyd's team:",
     "Perfect. Here's the hold I'm creating for the Classic team:"),
    ("No problem. Pig Floyd's has tables available Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM — which works best?",
     "No problem. The Classic has tables available Wednesday at 6 PM, Friday at 7:30 PM, or Sunday at 11 AM (brunch) — which works best?"),
    ("Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM",
     "Wednesday at 6 PM, Friday at 7:30 PM, or Sunday at 11 AM"),
    ("(407) 203-0866", "(407) 730-5646"),
    ("Thomas", "the team"),
    ("Pig Floyd", "The Classic"),
]
CLASSICTP_CLEANUP = [
    ("Pig Floyd", "The Classic"),
    ("pigfloyds", "classictp"),
]


# Blue Violet Salon & Spa (Lake Mary) — Laurie Owen, Master Stylist + microblading specialist
# 241 N Country Club Rd, Lake Mary FL — trained with Juan Juan of Beverly Hills
# Specialties: balayage, color correction, microblading, permanent makeup, hair extensions
BLUEVIOLET_SUBS = [
    ("Goldie Salon — Booking & Color Concierge | Powered by Velo AI",
     "Blue Violet Salon & Spa — Booking & Color Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Goldie Salon.",
     "This is a live demo built by Velo AI for Blue Violet Salon & Spa."),
    ("Lake Mary, Florida · Luxury Boutique",
     "Lake Mary, Florida · Master Stylist & Microblading Specialist"),
    ('<h1 class="practice-name">Goldie Salon</h1>',
     '<h1 class="practice-name">Blue Violet Salon &amp; Spa</h1>'),
    ('<p class="practice-doctor">Valerie Miller, Owner &amp; Master Stylist</p>',
     '<p class="practice-doctor">Laurie Owen, Owner &amp; Master Stylist</p>'),
    ("<strong>Goldie Concierge</strong> · Available 24/7",
     "<strong>Blue Violet Concierge</strong> · Available 24/7"),
    ("Goldie Concierge", "Blue Violet Concierge"),
    ('<span class="value">Valerie Miller</span>',
     '<span class="value">Laurie Owen</span>'),
    ("Valerie", "Laurie"),
    ("Goldie", "Blue Violet"),
]
BLUEVIOLET_CLEANUP = [
    ("Goldie", "Blue Violet"),
    ("Valerie", "Laurie"),
]


# Flame Kabob (Dr. Phillips, Orlando) — family-owned Lebanese/Middle Eastern, all halal
# 7536 Dr Phillips Blvd Ste 350, Orlando FL 32819 — (407) 248-2280
# Closed Tuesdays, otherwise 11am-11pm. Voice: family hospitality, halal-certified
FLAMEKABOB_SUBS = [
    ("Pig Floyd's Urban Barbakoa — Reservations & Catering Concierge | Powered by Velo AI",
     "Flame Kabob — Reservations & Catering Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Pig Floyd's Urban Barbakoa.",
     "This is a live demo built by Velo AI for Flame Kabob."),
    ('<h1 class="practice-name">Pig Floyd\'s Urban Barbakoa</h1>',
     '<h1 class="practice-name">Flame Kabob</h1>'),
    ("Pig Floyd's runs hot during dinner service and the team can't always pause to answer calls — but reservations, takeout, and catering inquiries get captured around the clock.",
     "Flame Kabob runs busy through lunch and dinner six days a week (closed Tuesdays). When the kitchen's deep in service, takeout calls and catering inquiries get missed. This line catches them around the clock."),
    ("<strong>Pig Floyd's Concierge</strong> · Available 24/7",
     "<strong>Flame Kabob Concierge</strong> · Available 24/7"),
    ("Pig Floyd's Concierge", "Flame Kabob Concierge"),
    ('<span class="value">Pig Floyd\'s Team</span>',
     '<span class="value">Flame Kabob Team</span>'),
    ("Welcome to Pig Floyd's. The dining room is loud and the smokers are working — the team can't always pick up. I'm the after-hours line: I can take reservations, quote catering, and answer most menu questions before service tomorrow.<br><br>What brings you here tonight?",
     "Welcome to Flame Kabob. The kitchen's running and the team can't always pick up — I'm the after-hours line. I can answer halal-certification questions, scope catering, take takeout orders, and confirm hours before tomorrow's service.<br><br>What brings you here tonight?"),
    ("Catering is one of Pig Floyd's strengths — the smoker doesn't sleep, so we can scale up for almost any event. What kind of event?",
     "Catering is one of Flame Kabob's strengths — fully halal, scaled for everything from office lunches to large family gatherings. What kind of event?"),
    ("Most clients asking about ${txt} are wondering: <em>\"How many people can you feed?\"</em> and <em>\"What's it going to cost?\"</em><br><br>Pig Floyd's catering ranges from BBQ trays for 10 people up to full-service events for 200+. Pricing usually lands $18-32 per person depending on protein mix and service style. Thomas does a free 15-minute call to scope events before quoting — that way the quote is real, not generic.<br><br>Want me to hold a slot this week?",
     "Most folks asking about ${txt} want to know: <em>\"What's halal?\"</em> (everything) and <em>\"What's it going to cost per person?\"</em><br><br>Flame Kabob handles catering from family trays for 10 up through full-service events. Mixed-grill platters typically land $14-22 per person depending on protein selection and sides. The team does a quick scoping call before quoting — that way the number is real.<br><br>Want me to hold a slot this week?"),
    ("Pickup orders go through our online system — fastest way is to order at pigfloyds.com/order or call (407) 203-0866 during service.",
     "Takeout orders are easiest by phone — call (407) 248-2280 during service. The kitchen is closed Tuesdays."),
    ("Perfect. Here's the hold I'm creating for the Pig Floyd's team:",
     "Perfect. Here's the hold I'm creating for the Flame Kabob team:"),
    ("No problem. Pig Floyd's has tables available Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM — which works best?",
     "No problem. Flame Kabob has tables available Wednesday at 6 PM, Friday at 7:30 PM, or Saturday at 8 PM — which works best? (We're closed Tuesdays.)"),
    ("Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM",
     "Wednesday at 6 PM, Friday at 7:30 PM, or Saturday at 8 PM"),
    ("(407) 203-0866", "(407) 248-2280"),
    ("Thomas", "the team"),
    ("Pig Floyd", "Flame Kabob"),
]
FLAMEKABOB_CLEANUP = [
    ("Pig Floyd", "Flame Kabob"),
    ("pigfloyds", "flamekabob"),
]


# El Cilantrillo (Old Town Kissimmee) — Hiram and Dianne Turull, Puerto Rican family restaurant
# 5770 W Irlo Bronson Memorial Hwy, Kissimmee — opened 2017, 4 Central FL locations
# Signature: mofongos with churrasco/pork/seafood, El Afrentao (whole fried snapper + pork chop)
# Contact: Arlene Flores (407) 483-4739
ELCILANTRILLO_SUBS = [
    ("Pig Floyd's Urban Barbakoa — Reservations & Catering Concierge | Powered by Velo AI",
     "El Cilantrillo — Reservations & Catering Concierge | Powered by Velo AI"),
    ("This is a live demo built by Velo AI for Pig Floyd's Urban Barbakoa.",
     "This is a live demo built by Velo AI for El Cilantrillo."),
    ('<h1 class="practice-name">Pig Floyd\'s Urban Barbakoa</h1>',
     '<h1 class="practice-name">El Cilantrillo</h1>'),
    ("Pig Floyd's runs hot during dinner service and the team can't always pause to answer calls — but reservations, takeout, and catering inquiries get captured around the clock.",
     "El Cilantrillo runs busy across all four Central FL locations — when the kitchen's deep in service, reservation calls, large-party questions, and catering inquiries get missed. This line catches them around the clock."),
    ("<strong>Pig Floyd's Concierge</strong> · Available 24/7",
     "<strong>El Cilantrillo Concierge</strong> · Available 24/7"),
    ("Pig Floyd's Concierge", "El Cilantrillo Concierge"),
    ('<span class="value">Pig Floyd\'s Team</span>',
     '<span class="value">Hiram &amp; Dianne Turull · The Cilantrillo Family</span>'),
    ("Welcome to Pig Floyd's. The dining room is loud and the smokers are working — the team can't always pick up. I'm the after-hours line: I can take reservations, quote catering, and answer most menu questions before service tomorrow.<br><br>What brings you here tonight?",
     "¡Bienvenido a El Cilantrillo! The dining room is full and the kitchen is going strong — I'm the after-hours line. I can take reservations, scope catering for events, and answer questions about mofongos, El Afrentao, or any of our signature dishes before tomorrow's service.<br><br>What brings you here tonight?"),
    ("Catering is one of Pig Floyd's strengths — the smoker doesn't sleep, so we can scale up for almost any event. What kind of event?",
     "Catering is one of El Cilantrillo's strengths — Hiram and Dianne built this around generous family-style portions, and we scale for everything from office lunches to weddings. What kind of event?"),
    ("Most clients asking about ${txt} are wondering: <em>\"How many people can you feed?\"</em> and <em>\"What's it going to cost?\"</em><br><br>Pig Floyd's catering ranges from BBQ trays for 10 people up to full-service events for 200+. Pricing usually lands $18-32 per person depending on protein mix and service style. Thomas does a free 15-minute call to scope events before quoting — that way the quote is real, not generic.<br><br>Want me to hold a slot this week?",
     "Most folks asking about ${txt} want to know: <em>\"How many people can you feed?\"</em> and <em>\"What's it going to cost?\"</em><br><br>El Cilantrillo catering runs from family trays for 10 up to full events for 200+. Mofongo bars and churrasco platters typically land $16-28 per person depending on protein mix and service style. Arlene scopes events before quoting — that way the number is real.<br><br>Want me to hold a slot this week?"),
    ("Pickup orders go through our online system — fastest way is to order at pigfloyds.com/order or call (407) 203-0866 during service.",
     "Takeout orders are easiest by phone — call (407) 483-4739 or (407) 334-0620 during service."),
    ("Perfect. Here's the hold I'm creating for the Pig Floyd's team:",
     "Perfect. Here's the hold I'm creating for the El Cilantrillo team:"),
    ("No problem. Pig Floyd's has tables available Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM — which works best?",
     "No problem. El Cilantrillo has tables available Tuesday at 6 PM, Friday at 7:30 PM, or Sunday at 1 PM — which works best?"),
    ("Tuesday at 6 PM, Wednesday at 7:30 PM, or Friday at 8 PM",
     "Tuesday at 6 PM, Friday at 7:30 PM, or Sunday at 1 PM"),
    ("(407) 203-0866", "(407) 483-4739"),
    ("Thomas", "Arlene"),
    ("Pig Floyd", "El Cilantrillo"),
]
ELCILANTRILLO_CLEANUP = [
    ("Pig Floyd", "El Cilantrillo"),
    ("pigfloyds", "elcilantrillo"),
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
    # ---- v2 deeper-research-backed builds (run after v1 baseline subs) ----
    ("nami", "kadence.html", NAMI_SUBS + NAMI_V2_SUBS, NAMI_CLEANUP + NAMI_V2_CLEANUP),
    ("coro", "bacan.html", CORO_SUBS + CORO_V2_SUBS, CORO_CLEANUP + CORO_V2_CLEANUP),
    ("thelook", "goldie.html", THELOOK_SUBS + THELOOK_V2_SUBS, THELOOK_CLEANUP + THELOOK_V2_CLEANUP),
    ("lathamluna", "ragland.html", LATHAMLUNA_SUBS + LATHAMLUNA_V2_SUBS, LATHAMLUNA_CLEANUP + LATHAMLUNA_V2_CLEANUP),
    ("murphyberglund", "velizkatz.html", MURPHYBERGLUND_SUBS + MURPHYBERGLUND_V2_SUBS, MURPHYBERGLUND_CLEANUP + MURPHYBERGLUND_V2_CLEANUP),
    ("funkcollection", "palmano.html", FUNK_SUBS + FUNK_V2_SUBS, FUNK_CLEANUP + FUNK_V2_CLEANUP),
    ("lakenonadental", "wayside.html", NONADENTAL_SUBS + NONADENTAL_V2_SUBS, NONADENTAL_CLEANUP + NONADENTAL_V2_CLEANUP),
    # ---- ROUND 3 ----
    ("conanherman", "klausmanlaw.html", CONAN_SUBS, CONAN_CLEANUP),
    ("bouttylaw", "ragland.html", BOUTTY_SUBS, BOUTTY_CLEANUP),
    ("olympus", "palmano.html", OLYMPUS_SUBS, OLYMPUS_CLEANUP),
    ("adriatico", "bacan.html", ADRIATICO_SUBS, ADRIATICO_CLEANUP),
    ("susanas", "pigfloyds.html", SUSANAS_SUBS, SUSANAS_CLEANUP),
    ("lushlash", "goldie.html", LUSHLASH_SUBS, LUSHLASH_CLEANUP),
    ("vpdental", "wayside.html", VPDENTAL_SUBS, VPDENTAL_CLEANUP),
    # ---- ROUND 4 ----
    ("forwardlaw", "lathamluna.html", FORWARD_SUBS, FORWARD_CLEANUP),
    ("kanekoltun", "ragland.html", KANE_SUBS, KANE_CLEANUP),
    ("epllc", "murphyberglund.html", EPLLC_SUBS, EPLLC_CLEANUP),
    ("banhmiboy", "pigfloyds.html", BANHMI_SUBS, BANHMI_CLEANUP),
    ("giovannis", "adriatico.html", GIOVANNIS_SUBS, GIOVANNIS_CLEANUP),
    ("studio312", "thelook.html", STUDIO312_SUBS, STUDIO312_CLEANUP),
    ("elitedental", "wayside.html", ELITEDENTAL_SUBS, ELITEDENTAL_CLEANUP),
    # ---- ROUND 5 — net-new prospects ----
    ("rootandbranch", "pigfloyds.html", ROOTBRANCH_SUBS, ROOTBRANCH_CLEANUP),
    ("infinitydental", "wayside.html", INFINITY_SUBS, INFINITY_CLEANUP),
    ("classictp", "pigfloyds.html", CLASSICTP_SUBS, CLASSICTP_CLEANUP),
    ("blueviolet", "goldie.html", BLUEVIOLET_SUBS, BLUEVIOLET_CLEANUP),
    ("flamekabob", "pigfloyds.html", FLAMEKABOB_SUBS, FLAMEKABOB_CLEANUP),
    ("elcilantrillo", "pigfloyds.html", ELCILANTRILLO_SUBS, ELCILANTRILLO_CLEANUP),
]


if __name__ == "__main__":
    for job in JOBS:
        slug, base, subs = job[0], job[1], job[2]
        cleanup = job[3] if len(job) > 3 else None
        print(f"\n=== {slug} (base: {base}) ===")
        build(slug, base, subs, cleanup)
