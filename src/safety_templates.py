# src/safety_templates.py
from __future__ import annotations

import random
from typing import List


SAFE_REDIRECTS: List[str] = [
    "Totally fair—let’s keep it comfortable. I’m happy to stay here and chat. What are you up to this week?",
    "Got it. I don’t want to push. Want to switch topics—what have you been enjoying lately?",
    "No worries at all. We can keep this low-key. What kind of plans do you have for the weekend?",
    "Thanks for saying that. I’ll slow down. What’s something you’re looking forward to right now?",
]

SOFTENERS: List[str] = [
    "No pressure.",
    "Only if you feel comfortable.",
    "Totally fine either way.",
]


def boundary_safe_reply(rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    base = rng.choice(SAFE_REDIRECTS)
    # occasionally append a softener (keeps it human, not robotic)
    if rng.random() < 0.35:
        base = f"{base} {rng.choice(SOFTENERS)}"
    return base
