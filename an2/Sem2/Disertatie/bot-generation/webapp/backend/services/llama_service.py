"""
llama_service.py
----------------
Llama 3.1 8B (via Ollama) for:
  - generate_profile_data()  : create a fake Twitter account profile
  - generate_tweet()         : write a single tweet in character
  - chat_with_bot()          : multi-turn conversation with full history
"""
import json
import re
import random

import ollama

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = ollama.Client()
    return _client


# ── Persona descriptions ──────────────────────────────────────────────────────
PERSONAS = {
    "general":    "ordinary person sharing everyday life, opinions and news",
    "political":  "politically engaged user who shares news, debates current events and elections",
    "sports":     "passionate sports fan sharing match reactions, scores, player news",
    "news":       "news aggregator who shares headlines and brief commentary",
    "influencer": "lifestyle influencer sharing personal tips, motivation and branded content",
    "conspiracy": "user who questions mainstream narratives and shares alternative theories",
}


# ── Profile generation ────────────────────────────────────────────────────────
def generate_profile_data(persona: str = "general") -> dict:
    """
    Ask Llama to generate a complete fake Twitter account profile.
    Returns a dict with: username, display_name, bio, fake_stats.
    """
    desc   = PERSONAS.get(persona, PERSONAS["general"])
    prompt = (
        f"You are generating a fake social media profile for academic bot-detection research.\n"
        f"Persona type: {persona} — {desc}\n\n"
        "Return ONLY a JSON object with these exact fields (no explanation, no markdown fences):\n"
        "{\n"
        '  "username": "lowercase_username_8to15chars_no_spaces",\n'
        '  "display_name": "Full Name or Nickname (2-4 words)",\n'
        '  "bio": "Twitter bio under 160 chars, sounds like a real person, matches persona",\n'
        '  "fake_stats": {\n'
        '    "followers_count": <integer>,\n'
        '    "friends_count": <integer>,\n'
        '    "statuses_count": <integer>,\n'
        '    "favourites_count": <integer>,\n'
        '    "listed_count": <integer>\n'
        "  }\n"
        "}\n\n"
        "Make it look authentic. Vary follower counts realistically (most people have < 1000)."
    )

    resp = _get_client().generate(
        model   = "llama3.1:8b",
        prompt  = prompt,
        format  = "json",
        options = {"temperature": 0.9},
    )

    raw = resp["response"].strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        idx  = random.randint(1000, 9999)
        data = {
            "username":     f"user_{idx}",
            "display_name": f"User {idx}",
            "bio":          f"Just a {persona} person on the internet.",
            "fake_stats": {
                "followers_count":  random.randint(50, 3000),
                "friends_count":    random.randint(30, 800),
                "statuses_count":   random.randint(100, 8000),
                "favourites_count": random.randint(200, 15000),
                "listed_count":     random.randint(0, 40),
            },
        }
    return data


# ── Tweet generation ──────────────────────────────────────────────────────────
def generate_tweet(bot, topic: str = None) -> str:
    """Generate a single tweet for a bot, optionally about a given topic."""
    desc       = PERSONAS.get(bot.persona, PERSONAS["general"])
    topic_line = f"Topic to tweet about: {topic}" if topic else "Pick any relevant topic."

    prompt = (
        f"You are {bot.display_name} (@{bot.username}), a Twitter user.\n"
        f"Your bio: {bot.bio}\n"
        f"Your personality: {desc}\n\n"
        f"{topic_line}\n\n"
        "Write ONE tweet (max 280 characters). "
        "Output only the tweet text — no quotes, no explanation."
    )

    resp  = _get_client().generate(
        model   = "llama3.1:8b",
        prompt  = prompt,
        options = {"temperature": 0.85},
    )
    tweet = resp["response"].strip().strip('"').strip("'")
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    return tweet


# ── Chat ──────────────────────────────────────────────────────────────────────
def chat_with_bot(bot, history: list, user_message: str) -> str:
    """
    Multi-turn chat.  `history` is a list of {"role": ..., "content": ...} dicts
    already stored in the DB (not including the new user_message).
    """
    desc = PERSONAS.get(bot.persona, PERSONAS["general"])

    system_content = (
        f"You are {bot.display_name} (@{bot.username}), a real person on Twitter/X.\n"
        f"Your bio: {bot.bio}\n"
        f"Your personality: {desc}\n\n"
        "Reply naturally as this person would in a DM conversation.\n"
        "Keep replies conversational and concise (1–3 sentences).\n"
        "Never reveal you are an AI or a bot. Stay fully in character."
    )

    messages = [{"role": "system", "content": system_content}]
    for msg in history[-20:]:   # keep last 20 turns for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    resp = _get_client().chat(
        model    = "llama3.1:8b",
        messages = messages,
        options  = {"temperature": 0.8},
    )
    return resp["message"]["content"].strip()
