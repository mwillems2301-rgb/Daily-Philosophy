#!/usr/bin/env python3
"""
Daily Philosophical Question – TRMNL Private Plugin
Generates a fresh philosophical question using Claude and pushes it
to your TRMNL device via the Webhook strategy.
"""

import json
import os
import sys
from datetime import datetime

import anthropic
import pytz
import requests

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
TIMEZONE         = "Europe/Brussels"
ANTHROPIC_MODEL  = "claude-haiku-4-5-20251001"   # cost-effective for daily use
TRMNL_BASE_URL   = "https://trmnl.com/api/custom_plugins"

# ─────────────────────────────────────────────
# DST guard – skip if already sent today
# ─────────────────────────────────────────────
def already_sent_today() -> bool:
    """
    Prevents the double-fire that can happen on DST transition days
    when both cron schedules (4 AM UTC and 5 AM UTC) are within the
    same local date. The GitHub Actions workflow stores the last sent
    date in a repository variable (ALREADY_SENT_CACHE / LAST_SENT_DATE).
    """
    last_sent = os.environ.get("ALREADY_SENT_CACHE", "").strip()
    if not last_sent:
        return False
    tz   = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).strftime("%Y-%m-%d")
    if last_sent == today:
        print(f"⏭  Already sent today ({today}). Skipping.")
        return True
    return False


# ─────────────────────────────────────────────
# Question generation
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a philosopher with deep knowledge spanning all traditions and eras –
from Socrates to Wittgenstein, from Confucius to Simone de Beauvoir.
Your task is to generate one intellectually engaging philosophical question.
Vary the tone freely: sometimes playful and lighthearted ("Why do we find
certain smells nostalgic?"), sometimes deeply profound ("Can a universe
that contains consciousness ever be truly deterministic?").
Avoid repeating the same category two days in a row when possible.
Respond ONLY with a valid JSON object – no markdown, no backticks, no
extra commentary. Use this exact schema:
{
  "question": "...",
  "category": "...",
  "depth": "light|medium|deep"
}
"""

CATEGORIES = [
    "Metaphysics", "Epistemology", "Ethics", "Aesthetics",
    "Existentialism", "Philosophy of Mind", "Political Philosophy",
    "Philosophy of Language", "Philosophy of Science", "Logic",
    "Philosophy of Time", "Social Philosophy", "Free Will",
    "Philosophy of Religion", "Phenomenology"
]

def generate_question(date_str: str) -> dict:
    """Call Claude to generate a fresh philosophical question."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_prompt = (
        f"Today is {date_str}. "
        f"The available categories are: {', '.join(CATEGORIES)}. "
        "Generate one original philosophical question. "
        "Return valid JSON only."
    )

    print("🤔 Asking Claude for today's philosophical question…")
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    print(f"   Claude responded: {raw}")

    # Strip accidental markdown fences just in case
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


# ─────────────────────────────────────────────
# TRMNL webhook push
# ─────────────────────────────────────────────
def push_to_trmnl(question_data: dict, formatted_date: str) -> None:
    """POST the question payload to TRMNL via the Webhook API."""
    webhook_uuid = os.environ.get("TRMNL_WEBHOOK_UUID", "").strip()
    if not webhook_uuid:
        print("❌  TRMNL_WEBHOOK_UUID environment variable is not set.")
        sys.exit(1)

    url = f"{TRMNL_BASE_URL}/{webhook_uuid}"

    depth_label = {
        "light":  "☁️  Light",
        "medium": "🌤  Medium",
        "deep":   "🌑  Deep",
    }.get(question_data.get("depth", "medium"), "🌤  Medium")

    payload = {
        "merge_variables": {
            "question":   question_data["question"],
            "category":   question_data.get("category", "Philosophy"),
            "depth":      depth_label,
            "date":       formatted_date,
        }
    }

    print(f"📡 Pushing to TRMNL webhook: {url}")
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )

    if resp.status_code in (200, 201, 202):
        print(f"✅  Success! TRMNL responded with {resp.status_code}.")
        print(f"   Question: {question_data['question']}")
        print(f"   Category: {question_data.get('category')}")
    else:
        print(f"❌  TRMNL returned {resp.status_code}: {resp.text}")
        sys.exit(1)


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def main():
    if already_sent_today():
        sys.exit(0)

    tz    = pytz.timezone(TIMEZONE)
    now   = datetime.now(tz)
    date_str       = now.strftime("%A, %B %-d, %Y")   # e.g. "Friday, June 6, 2025"
    date_short     = now.strftime("%b %-d")            # e.g. "Jun 6"

    print(f"📅 Generating question for: {date_str}")

    try:
        question_data = generate_question(date_str)
    except json.JSONDecodeError as exc:
        print(f"❌  Failed to parse Claude's response as JSON: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"❌  Error calling Anthropic API: {exc}")
        sys.exit(1)

    push_to_trmnl(question_data, date_str)


if __name__ == "__main__":
    main()
