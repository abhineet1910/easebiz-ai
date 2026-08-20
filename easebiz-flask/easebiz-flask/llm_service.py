"""
Talks to a free LLM (Groq's OpenAI-compatible API, https://console.groq.com) to generate
the narrative parts of the business analysis (market size, expert advice, etc).

Factual data that shouldn't be hallucinated -- license fees, timelines, government scheme
links -- stays as static, verified data in pdf_generator.py / the templates, and is NOT
sent through the LLM.

If GROQ_API_KEY isn't set, or the API call fails for any reason, this silently falls back
to solid static copy so the app always works out of the box.

Swapping providers: any OpenAI-compatible free/cheap endpoint works here (Groq, OpenRouter,
local Ollama, Google AI Studio's Gemini via its OpenAI-compat endpoint, etc) -- just change
GROQ_URL / GROQ_MODEL / the auth header below.
"""

import json
import os

import requests

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = """You are the analysis engine behind EaseBiz AI, a platform that gives \
Indian entrepreneurs a compliance and growth roadmap. Given a business type, return ONLY \
valid JSON (no markdown fences, no commentary) matching EXACTLY this schema:

{
  "market_size": "2-3 sentences on Indian market size (an INR crore figure) and CAGR",
  "consumer_behavior": "2-3 sentences on consumer behaviour and adoption trends",
  "ai_insight": "1-2 sentence strategic insight with a concrete percentage claim",
  "expert_quote": "one punchy first-person-sounding line of founder advice, under 220 chars",
  "financial_advice": "1-2 sentences",
  "operational_advice": "1-2 sentences",
  "legal_advice": "1-2 sentences",
  "local_competitors": "1-2 sentences on Indian competitors and the local advantage",
  "global_competitors": "1-2 sentences on global benchmarks and export potential"
}

Tone: confident, specific to the given business type, written for a founder. Do not include \
any text outside the JSON object."""


def _fallback_analysis(business_type: str) -> dict:
    """Used when no API key is configured or the live call fails."""
    return {
        "market_size": (
            f"The Indian market for {business_type} is currently valued at approximately "
            "Rs 45,000 Crores, with a projected CAGR of 18.5% over the next 5 years. Urban "
            "adoption leads demand, while Tier-2 and Tier-3 cities are the next frontier."
        ),
        "consumer_behavior": (
            "Consumers are shifting toward digital-first experiences, with a strong "
            "preference for transparency, sustainability, and localized support."
        ),
        "ai_insight": (
            f"{business_type} ventures with strong social proof and referral loops see up "
            "to 40% lower customer acquisition costs."
        ),
        "expert_quote": (
            "The biggest mistake new founders make is underestimating the regulatory "
            "compliance timeline. Start your Udyam and GST filings on Day 1."
        ),
        "financial_advice": "Maintain a clean burn rate and aim for profitability within 18-24 months.",
        "operational_advice": "Automate your supply chain early and use AI for inventory forecasting.",
        "legal_advice": "Protect your IP and file trademarks before public launch.",
        "local_competitors": (
            "Reliance, Tata Digital, and emerging D2C brands lead a fragmented but "
            "consolidating market; regional logistics know-how is the key moat."
        ),
        "global_competitors": (
            "Amazon, Shopify, and specialised vertical players set the benchmark abroad, "
            "with strong export demand from the Middle East and Southeast Asia."
        ),
    }


def generate_business_analysis(business_type: str) -> dict:
    fallback = _fallback_analysis(business_type)

    if not GROQ_API_KEY:
        return fallback

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "temperature": 0.6,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Business type: {business_type}"},
                ],
            },
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)

        # Guarantee every expected key exists even if the model drops one
        for key, value in fallback.items():
            data.setdefault(key, value)
        return data
    except Exception:
        return fallback
