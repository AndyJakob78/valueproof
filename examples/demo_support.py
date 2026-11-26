"""Demo: answering support tickets with three models working together.

    1. read      - cheap model pulls order id, issue and mood out of the ticket
    2. reply     - Scout & Rescue: cheap model drafts, strong model only if the
                   draft fails a code check
    3. summary   - mid-size model writes one summary for the whole batch

Run without an API key (stub models, made-up costs):
    python examples/demo_support.py

Run against Claude (real calls, real cost - a few cents):
    python examples/demo_support.py --live
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline import Step, run_pipeline  # noqa: E402
from scout_rescue import ModelResult  # noqa: E402

TICKETS = [
    "Hi, order #48213 arrived with a cracked screen. Can I get a replacement?",
    "Where is my parcel?? Order 77120, it's been 9 days. Really annoyed.",
    "I was charged twice for order #50911 and also the invoice shows the wrong "
    "company name, and I need it fixed before our audit on Friday.",
]


# ---------- checks: plain code, no model call ----------

def check_read(text: str, data: dict) -> str | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return "not valid JSON"
    missing = [k for k in ("order_id", "issue", "mood") if not data.get(k)]
    return f"missing {', '.join(missing)}" if missing else None


def check_reply(text: str, data: dict) -> str | None:
    order_id = json.loads(data["read"])["order_id"]
    if len(text.strip()) < 60:
        return "too short"
    if order_id not in text:
        return "does not mention the order id"
    if "[" in text or "TODO" in text:
        return "contains a placeholder"
    return None


# ---------- prompts ----------

def read_prompt(data: dict) -> str:
    return (
        "Extract JSON with keys order_id (digits only), issue (max 10 words) and "
        "mood (calm|annoyed|urgent) from this support ticket. Reply with JSON only.\n\n"
        + data["ticket"]
    )


def reply_prompt(data: dict) -> str:
    facts = json.loads(data["read"])
    return (
        "Write a short, friendly support reply (3-5 sentences). Mention the order "
        f"number {facts['order_id']}, address the issue: {facts['issue']}. "
        f"The customer is {facts['mood']}. No placeholders.\n\nTicket:\n{data['ticket']}"
    )


# ---------- models ----------

def stub(model: str, cost: float, reply_fn):
    def call(prompt: str) -> ModelResult:
        return ModelResult(reply_fn(prompt), cost, model)
    return call


def stub_models():
    def read(prompt):
        ticket = prompt.split("\n\n", 1)[1]
        order_id = "".join(c for c in ticket.split("rder")[1][:8] if c.isdigit())
        mood = "urgent" if "audit" in ticket else "annoyed" if "annoyed" in ticket else "calm"
        return json.dumps({"order_id": order_id, "issue": ticket[:60], "mood": mood})

    def cheap_reply(prompt):
        order_id = prompt.split("order number ")[1].split(",")[0]
        if "charged twice" in prompt:  # the hard case: the cheap model gets it wrong
            return "Sorry about that! We'll look into it."
        return (f"Thanks for reaching out about order {order_id}. We're sorry for the trouble "
                "and have started a fix; you'll get an update by email within 24 hours.")

    def strong_reply(prompt):
        order_id = prompt.split("order number ")[1].split(",")[0]
        return (f"Thanks for flagging order {order_id}. We've refunded the duplicate charge and "
                "issued a corrected invoice with the right company name; both reach you before Friday.")

    return {
        "cheap": stub("cheap-model", 0.0004, read),
        "scout": stub("cheap-model", 0.0006, cheap_reply),
        "rescue": stub("strong-model", 0.0150, strong_reply),
        "mid": stub("mid-model", 0.0040, lambda p: "3 tickets: 1 damage, 1 delay, 1 billing (urgent)."),
    }


def live_models():
    from claude_models import claude

    return {
        "cheap": claude("claude-haiku-5-5", effort="low"),
        "scout": claude("claude-haiku-5-5", effort="low"),
        "rescue": claude("claude-opus-5-5", effort="medium"),
        "mid": claude("claude-sonnet-5-5", effort="low"),
    }


def main() -> None:
    models = live_models() if "--live" in sys.argv else stub_models()

    steps = [
        Step("read", read_prompt, scout=models["cheap"], rescue=models["rescue"], check=check_read),
        Step("reply", reply_prompt, scout=models["scout"], rescue=models["rescue"], check=check_reply),
    ]

    total = 0.0
    replies = []
    for ticket in TICKETS:
        run = run_pipeline(steps, {"ticket": ticket})
        for entry in run.log:
            note = f"  ({entry.note})" if entry.note else ""
            print(f"{entry.step:<6} {entry.path:<6} {entry.model:<18} ${entry.cost_usd:.4f}{note}")
        print("reply:", run.data["reply"], "\n")
        total += run.cost_usd
        replies.append(run.data["reply"])

    summary = models["mid"]("Summarize these support replies for the team lead in one line:\n" + "\n".join(replies))
    total += summary.cost_usd
    print(f"summary       {summary.model:<18} ${summary.cost_usd:.4f}\n{summary.text}\n")
    print(f"Total for {len(TICKETS)} tickets: ${total:.4f}")


if __name__ == "__main__":
    main()
