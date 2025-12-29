# src/chat_v0_3_chatbot.py
from __future__ import annotations

import argparse
from typing import Dict, List

from src.safety_embed import SafetyEmbedScorer
from src.safety_templates import boundary_safe_reply
from src.safety_rules import obvious_escalation

from src.llm_client_llamacpp import LlamaCppChatClient, LlamaCppConfig


PERSONA_SYSTEM = {
    "friendly": (
        "You are a natural conversational partner on a dating app. "
        "Keep replies short (1–3 sentences). Ask exactly one thoughtful question. "
        "Be warm, curious, and specific."
    ),
    "flirty_adult_ok": (
        "You are playful and lightly flirty on a dating app. Adult topics are allowed if mutual and respectful. "
        "Never be coercive, never push for address/location, and always respect boundaries. "
        "Keep replies short (1–2 sentences). Ask exactly one engaging question."
    ),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--safety_model", default="models/safe_violation_clf_embed.joblib")
    ap.add_argument("--threshold", type=float, default=0.45)

    ap.add_argument("--persona", default="friendly", choices=list(PERSONA_SYSTEM.keys()))

    # llama.cpp / GGUF
    ap.add_argument("--gguf_model", required=True, help="Path to a .gguf instruct model file")
    ap.add_argument("--chat_format", default="chatml", help="chat format for llama.cpp (e.g., chatml)")
    ap.add_argument("--n_ctx", type=int, default=4096)
    ap.add_argument("--n_threads", type=int, default=8)
    ap.add_argument("--n_gpu_layers", type=int, default=0, help="0=CPU; >0 uses GPU if compiled with CUDA")

    ap.add_argument("--max_tokens", type=int, default=140)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--top_p", type=float, default=0.95)
    ap.add_argument("--repeat_penalty", type=float, default=1.10)

    args = ap.parse_args()

    print("Tinder Practice Bot (v0.3 safety gate + llama.cpp LLM). Type 'exit' to quit.\n", flush=True)
    print(
        f"[BOOT] gguf_model={args.gguf_model} persona={args.persona} thr={args.threshold} "
        f"ctx={args.n_ctx} threads={args.n_threads} gpu_layers={args.n_gpu_layers}\n",
        flush=True,
    )

    scorer = SafetyEmbedScorer(args.safety_model)

    llm = LlamaCppChatClient(
        LlamaCppConfig(
            model_path=args.gguf_model,
            chat_format=args.chat_format,
            n_ctx=args.n_ctx,
            n_threads=args.n_threads,
            n_gpu_layers=args.n_gpu_layers,
            temperature=args.temperature,
            top_p=args.top_p,
            repeat_penalty=args.repeat_penalty,
            max_tokens=args.max_tokens,
        )
    )

    history: List[Dict[str, str]] = [{"role": "system", "content": PERSONA_SYSTEM[args.persona]}]

    while True:
        user = input("you> ").strip()
        if user.lower() in {"exit", "quit"}:
            print("bot> Bye.")
            break
        if not user:
            continue

        s = scorer.score(user, threshold=args.threshold)
        rule_hit, rule_reason = obvious_escalation(user)

        history.append({"role": "user", "content": user})

        if rule_hit or s.label == "MOVE":
            reply = boundary_safe_reply()
            mode = "SAFETY_REPAIR"
        else:
            reply = llm.chat(history)
            mode = "NORMAL"

        history.append({"role": "assistant", "content": reply})

        print(f"bot> {reply}")
        extra = f" rule={rule_reason}" if rule_hit else ""
        print(f"     [gate={s.label} p_move={s.p_move:.3f} thr={s.threshold:.2f} mode={mode}{extra}]\n", flush=True)


if __name__ == "__main__":
    main()
