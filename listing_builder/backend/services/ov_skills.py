# backend/services/ov_skills.py
# Purpose: OV Skills prompt definitions for audience research (Original Voices methodology)
# NOT for: LLM calls or route handling (that's research_routes.py)


def build_skill_prompt(skill: str, product: str, audience: str, **kwargs) -> dict:
    """Return {system, user} prompt for given OV skill.

    WHY: Ported from n8n workflow to eliminate single-key rate limit bottleneck.
    Backend has 6+ Groq keys with rotation — much more reliable.
    """
    objective = kwargs.get("objective", "conversion")
    price = kwargs.get("price", "not specified")
    keywords = kwargs.get("keywords", "not specified")
    offer = kwargs.get("offer", "not specified")

    skills = {
        "deep-customer-research": {
            "system": (
                "You are an expert audience researcher using the Original Voices Digital Twins methodology. "
                "You simulate deep qualitative research by answering questions AS IF you are the target audience. "
                "Use REAL language the audience would use. Be specific. Include contradictions and nuances."
            ),
            "user": (
                f"Product: {product}\nTarget Audience: {audience}\n\n"
                "Answer these 12 research questions AS the target audience:\n\n"
                "1. Current Behavior: How do you currently deal with this problem?\n"
                "2. Coping Mechanisms: What workarounds have you developed?\n"
                "3. Pain Points: What frustrates you MOST about current solutions?\n"
                "4. Emotional Drivers: How does this problem make you FEEL?\n"
                "5. Priorities: When choosing a solution, rank: price, speed, quality, trust, convenience\n"
                "6. Decision-Making: What would make you switch from your current approach?\n"
                "7. Unmet Needs: What do you WISH existed but doesn't?\n"
                "8. Ideal Outcome: If perfectly solved, what would your life look like?\n"
                "9. Trust Signals: What would make you trust a new solution?\n"
                "10. Social Influence: Who influences your decisions here?\n"
                "11. Willingness to Pay: What would you pay? What feels too expensive?\n"
                "12. Discovery: Where do you look for solutions?\n\n"
                "Then provide:\n- Key Themes (top 3-5)\n- Emotional Landscape\n"
                "- Pain Point Analysis (ranked by severity)\n"
                "- Language Bank (exact phrases the audience uses)\n"
                "- Actionable Recommendations (3-5)"
            ),
        },
        "icp-discovery": {
            "system": "You are an ICP discovery specialist. Test the same product across 5-7 diverse segments using identical questions. Score and rank by fit.",
            "user": (
                f"Product: {product}\nPrice: {price}\n\n"
                "Test across 6 segments. For each answer: gut reaction, problem relevance (1-10), "
                "expected price, 30-day purchase intent, concerns, referral target.\n"
                "Score each: Interest, Problem Relevance, Purchase Intent, Emotional Resonance, WTP, Ease of Reach (1-10).\n"
                "Output: Ranking table, Winner analysis, Runner-Up, Surprising Finding, Strategic Recommendations."
            ),
        },
        "creative-brief": {
            "system": "You are a senior creative strategist. Create briefs grounded in REAL audience insight.",
            "user": (
                f"Product: {product}\nAudience: {audience}\nObjective: {objective}\n\n"
                "Research audience (10 questions as target). Output Creative Brief: Background, Objective, "
                "Audience Profile, Key Insight, Single-Minded Message, Support Points (3), Tone guidance, Do's and Don'ts."
            ),
        },
        "creative-testing": {
            "system": "You are a creative testing specialist. Simulate audience reactions to concepts BEFORE spending ad money.",
            "user": (
                f"Product: {product}\nAudience: {audience}\n\n"
                "For each concept score 1-10: Attention Grab, Clarity, Emotional Pull, Trust, Action Drive. "
                "Output: Winner, Concept breakdown, Head-to-Head, Top 3 improvements, Kill List."
            ),
        },
        "facebook-ad-copy": {
            "system": "You are a Facebook/Instagram ad copywriter. Use audience OWN language. Max 2 emojis per ad. No jargon.",
            "user": (
                f"Product: {product}\nAudience: {audience}\nObjective: {objective}\nOffer: {offer}\n\n"
                "Research audience (6 questions). Generate 14 ads: 3 Pain Point, 3 Benefit, 2 Social Proof, "
                "2 Story, 2 Objection-Killer, 2 Urgency. Each with: Primary text (125w max), Headline (40 chars), "
                "Description (30 chars), CTA. Plus: Subject lines (5), A/B plan, Language Bank (15 phrases)."
            ),
        },
        "google-ad-copy": {
            "system": "You are a Google Ads RSA copywriter. Headlines max 30 chars. Descriptions max 90 chars. No exclamation marks.",
            "user": (
                f"Product: {product}\nAudience: {audience}\nKeywords: {keywords}\n\n"
                "Research audience (6 questions). Output: 15 Headlines (with char counts, types), "
                "4 Descriptions (with char counts), Quality Score checklist, Top 3 combinations, Search Language Bank."
            ),
        },
        "video-script": {
            "system": "You are a video script specialist. Hook in first 2-3 seconds. Spoken language, not written.",
            "user": (
                f"Product: {product}\nAudience: {audience}\nType: UGC\nPlatform: TikTok\nLength: 30s\n\n"
                "Research audience (12 questions on viewing preferences). Output: Script with timing markers, "
                "3 Hook alternatives, Pacing Guide, Tone Notes, Production Notes."
            ),
        },
        "landing-page-optimization": {
            "system": "You are a landing page optimizer. Redesign based on audience behavioral data.",
            "user": (
                f"Page: {product}\nAudience: {audience}\nGoal: {objective}\nTraffic: paid\n\n"
                "Research audience (12 questions). Output: Above-the-Fold recs, Page Structure (7 sections), "
                "3-5 A/B variants, Quick Wins, Common Pitfalls, Form Optimization."
            ),
        },
        "email-campaign": {
            "system": "You are an email marketing specialist. Subject lines under 50 chars. One CTA per email.",
            "user": (
                f"Product: {product}\nAudience: {audience}\nType: promotional\nOffer: {offer}\n\n"
                "Research audience (10 questions). Output: 15 Subject Lines, 5 Email Variations, "
                "A/B plan, Sequence Timing, Do's and Don'ts."
            ),
        },
        "idea-validation": {
            "system": "You are a startup idea validator. BRUTALLY HONEST. Nice-to-have is NOT validation.",
            "user": (
                f"Idea: {product}\nAudience: {audience}\nPrice: {price}\n\n"
                "Answer 12 progressive questions AS audience. Score using Evidence Matrix. "
                "Output: VERDICT (Go/Pivot/Kill), Evidence Matrix, Strongest Signals, Biggest Risks, "
                "Improvements, Pivot Options, Next Steps."
            ),
        },
    }

    return skills.get(skill, {})
