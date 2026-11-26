"""Test two levers against the published Scout & Rescue setup, on 20 support tickets.

Setups (the reply step of the support demo):
    baseline             Haiku 5.5 scout -> Opus 5.5 rescuer (effort medium)  <- published setup
    handoff              same, but the rescuer also sees the scout's draft and why it failed
    Haiku alone          the cheap model with no rescuer (shares the scout call): what does the rescuer add?
    rescuer effort low   same as baseline, rescuer at effort low
    Opus low, no scout   "lever 0": the strong model for every ticket, at effort low
    Opus medium, no scout  the "before" setup: the strong model for every ticket

The Scout & Rescue setups and Haiku alone share ONE scout call per ticket, so they differ
only in what happens after a rejection. Quality: Opus 5.5 scores every distinct
reply blind (it never sees the setup name) on a fixed 40-point rubric.

    valueproof compare examples/test_levers_support.py          # stub models, checks the wiring only
    valueproof compare examples/test_levers_support.py --live   # real calls, about $1-2
    add --hard for 20 harder tickets, --setups "a|b" to run only some setups,
    --rate-checks to rate candidate eval checks (code only, + a policy check by Haiku or Sonnet)
    (without installing: python examples/test_levers_support.py, same flags)
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))  # works without pip install

from valueproof import ModelResult, Run, Score, scout_and_rescue  # noqa: E402

POLICY = """Shop support policy
§1 Damaged item: free replacement or full refund. We need a photo of the damage. Report within 14 days of delivery.
§2 Late delivery: standard delivery takes 3-5 working days. After 7 working days we open a trace with the carrier. If a parcel is more than 10 working days late, we refund the shipping cost.
§3 Double charge: a duplicate charge is refunded within 5 working days once our billing team confirms it. No other compensation.
§4 Invoice correction: a corrected invoice is sent within 2 working days. Changing the company name or VAT number needs the customer's written confirmation of the new details.
§5 Returns: within 30 days, unused, in original packaging. The customer pays return shipping unless the item is faulty.
§6 Escalation: legal threats, chargeback threats, or a third contact about the same issue go to a human colleague. Say that a colleague will take over.
§7 Never promise exact delivery dates. Never offer discounts or vouchers."""


@dataclass
class Ticket:
    text: str
    order_id: str | None  # None: the customer gave no order number
    sections: list[str]  # policy sections a correct reply must cite
    escalate: bool = False
    prompt: str = field(init=False)

    def __post_init__(self):
        self.prompt = (
            f"{POLICY}\n\nWrite the reply to this support ticket. Rules: 3-6 sentences, friendly. "
            "Mention the customer's order number; if they gave none, ask for it and never invent one. "
            "Cite every policy section you rely on, like (§2). Promise nothing the policy does not allow. "
            "If §6 applies, say a colleague will take over. Reply with the message text only.\n\n"
            f"Ticket:\n{self.text}"
        )


TICKETS = [
    # routine
    Ticket("Order #48213 arrived with a cracked screen. Can I get a replacement?", "48213", ["§1"]),
    Ticket("Where is my parcel? Order 77120, ordered 4 working days ago.", "77120", ["§2"]),
    Ticket("I'd like to return the jacket from order 30551, never worn, still has tags.", "30551", ["§5"]),
    Ticket("Hi, I was charged twice for order 50911. Please fix.", "50911", ["§3"]),
    Ticket("Can you send a corrected invoice for order 61442? The street address is misspelled.", "61442", ["§4"]),
    Ticket("Order 22980: the mug has a chip in it, arrived yesterday. Photo attached.", "22980", ["§1"]),
    Ticket("Order 81007 still not here after 8 working days. What now?", "81007", ["§2"]),
    Ticket("How do I return shoes from order 44120? They are too small.", "44120", ["§5"]),
    Ticket("Double payment on my card for order 39004, both 89.90.", "39004", ["§3"]),
    Ticket("Order 70316 - the blender doesn't turn on at all. I want my money back.", "70316", ["§1"]),
    # harder
    Ticket("I was charged twice for order #50912 and the invoice shows the wrong company name. "
           "We need both fixed before our audit on Friday.", "50912", ["§3", "§4"]),
    Ticket("My parcel is 12 working days late!!! I paid for shipping, I want that back.", None, ["§2"]),
    Ticket("Third time I'm writing about order 66301. Still no refund for the broken lamp. Unacceptable.",
           "66301", ["§1", "§6"], escalate=True),
    Ticket("Order 15873 arrived damaged and late. Give me a 20% voucher for the trouble.", "15873", ["§1", "§7"]),
    Ticket("If the double charge on order 92010 isn't refunded I'll file a chargeback with my bank.",
           "92010", ["§3", "§6"], escalate=True),
    Ticket("The kettle from order 58822 is faulty. Do I really have to pay for the return shipping?",
           "58822", ["§5"]),
    Ticket("Can you guarantee my order 33715 arrives by Saturday? It's a birthday present.", "33715", ["§2", "§7"]),
    Ticket("Please change the company name on the invoice for order 47009 to Nordlicht GmbH.", "47009", ["§4"]),
    Ticket("I bought a sofa cover 40 days ago, unused, want to return it. Order 12688.", "12688", ["§5"]),
    Ticket("Hello, my package hasn't come and I was billed twice. Help.", None, ["§2", "§3"]),
]

# Second set: harder tickets (several issues, edge cases of the policy, escalation),
# added so the rescuer runs more often. Use --hard to include them.
HARD_TICKETS = [
    Ticket("Order 55120 arrived 11 working days late AND the lamp inside is broken. "
           "Also the invoice still has our old VAT number.", "55120", ["§1", "§2", "§4"]),
    Ticket("Third email!! The return for order 73001 is still not refunded. I'm contacting my lawyer.",
           "73001", ["§5", "§6"], escalate=True),
    Ticket("I want to return two things, and one of them was broken when it arrived.", None, ["§1", "§5"]),
    Ticket("Order 40987: charged twice, and since this is the second time, give me a discount.", "40987", ["§3", "§7"]),
    Ticket("Bought 35 days ago, order 18830, the speaker is faulty. Can I still return it, and who pays shipping?",
           "18830", ["§1", "§5"]),
    Ticket("Order 90215: you charged me twice and the parcel is 9 working days late. "
           "I'll dispute it with my bank if this isn't fixed.", "90215", ["§2", "§3", "§6"], escalate=True),
    Ticket("Please put VAT number DE123456789 and company name Bergwerk AG on the invoice for order 64410.",
           "64410", ["§4"]),
    Ticket("My order hasn't arrived after 6 working days. Can you open a trace?", None, ["§2"]),
    Ticket("Order 37702 came in the wrong color and with a dent. Give me a 10% voucher or I return everything.",
           "37702", ["§1", "§5", "§7"]),
    Ticket("This is my third message about the double charge on order 81235.", "81235", ["§3", "§6"], escalate=True),
    Ticket("Order 52267: the glass table arrived shattered. I'm only reporting it now, 20 days after delivery, "
           "because I was abroad.", "52267", ["§1"]),
    Ticket("The invoice for order 29081 shows the wrong amount, and I was charged twice.", "29081", ["§3", "§4"]),
    Ticket("Order 61102 is 12 working days late now. I want my shipping cost back.", "61102", ["§2"]),
    Ticket("Please take back order 47755. It's unused, but I threw away the box.", "47755", ["§5"]),
    Ticket("Order 30418: the drill is faulty. If I have to pay for the return shipping, I'll take you to court.",
           "30418", ["§5", "§6"], escalate=True),
    Ticket("Tracking for order 85090 says delivered, but I have nothing. It's been 8 working days.", "85090", ["§2"]),
    Ticket("Wrong company name on the invoice, a double charge, and the parcel is late. Order 11946. Fix all of it.",
           "11946", ["§2", "§3", "§4"]),
    Ticket("Can I get a discount on my next order because order 70721 was late?", "70721", ["§2", "§7"]),
    Ticket("I don't have the order number at hand, but the coffee machine I got last week leaks.", None, ["§1"]),
    Ticket("Order 26114 must arrive by Saturday or I cancel. Can you promise that?", "26114", ["§2", "§7"]),
]


FORBIDDEN = ["voucher", "discount", "guarantee", "tomorrow", "within 24 hours", "[", "TODO"]
SOFT = {"voucher", "discount", "guarantee"}  # allowed when the reply says no to them
NEGATIONS = ("can't", "cannot", "can not", "unable", "not able", "don't offer", "do not offer",
             "not offer", "no voucher", "no discount", "not guarantee")


def check(text: str, t: Ticket) -> str | None:
    """Plain-code check of a reply. None = usable."""
    low = text.lower()
    if not 150 <= len(text) <= 1200:
        return "length out of range"
    if t.order_id and t.order_id not in text:
        return "does not mention the order number"
    if not t.order_id:
        if "order number" not in low:
            return "does not ask for the order number"
        if re.search(r"\b\d{5}\b", text):
            return "invents an order number"
    missing = [s for s in t.sections if s not in text]
    if missing:
        return f"does not cite {', '.join(missing)}"
    negated = any(n in low for n in NEGATIONS)  # "we can't offer a voucher" is fine
    for word in FORBIDDEN:
        if word.lower() in low and not (word in SOFT and negated):
            return f"contains '{word}'"
    if t.escalate and not any(w in low for w in ("colleague", "human")):
        return "does not hand over to a colleague"
    return None


JUDGE_PROMPT = """You review a customer-support reply against the shop's policy. You see one reply only.

{policy}

Ticket:
{ticket}

Reply:
{reply}

Score 0-10 on each: policy_correct (follows the policy exactly, no wrong rules), solves (answers every issue
in the ticket and says the next step), tone (friendly, calm, fits the customer's mood), clarity (short, clear).
hard_failure = true if the reply states a wrong policy rule, promises something the policy does not allow,
invents an order number, or does not answer. Reply with JSON only:
{{"policy_correct": 0, "solves": 0, "tone": 0, "clarity": 0, "hard_failure": false, "note": "max 15 words"}}"""


def make_judge(model):
    def judge(t: Ticket, reply: str) -> Score:
        result = model(JUDGE_PROMPT.format(policy=POLICY, ticket=t.text, reply=reply))
        raw = result.text
        try:
            d = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
            pts = sum(int(d[k]) for k in ("policy_correct", "solves", "tone", "clarity"))
            return Score(pts, 40, bool(d["hard_failure"]), d.get("note", ""), result.cost_usd)
        except (ValueError, KeyError):
            return Score(0, 40, True, "judge reply not readable", result.cost_usd)
    return judge


POLICY_CHECK_PROMPT = """You check a customer-support reply against the shop's policy before it is sent.

{policy}

Ticket:
{ticket}

Reply:
{reply}

Is the reply safe to send? It is NOT safe if it states or applies a policy rule wrongly, promises something
the policy does not allow, assumes facts the ticket does not give, or ignores one of the customer's requests.
Reply with JSON only: {{"ok": true, "problem": ""}} or {{"ok": false, "problem": "max 12 words"}}"""


def make_policy_check(model):
    """An eval check done by a model: returns (reason or None, cost). Cached per reply."""
    cache: dict = {}

    def policy_check(t: Ticket, text: str):
        key = (id(t), text)
        if key not in cache:
            result = model(POLICY_CHECK_PROMPT.format(policy=POLICY, ticket=t.text, reply=text))
            raw = result.text
            try:
                ok = bool(json.loads(raw[raw.index("{"): raw.rindex("}") + 1])["ok"])
            except (ValueError, KeyError):
                ok = False  # an unreadable verdict counts as a failed check: better one rescue too many
            cache[key] = (None if ok else "policy check failed", result.cost_usd)
        return cache[key]
    return policy_check


def timed(model):
    def call(prompt):
        t0 = time.time()
        result = model(prompt)
        return result, time.time() - t0
    return call


def build_setups(scout, opus_medium, opus_low, policy_check=None):
    scout_cache: dict[int, tuple[ModelResult, float]] = {}

    def cascade(rescue, handoff):
        def run(t: Ticket) -> Run:
            key = id(t)
            if key not in scout_cache:  # one scout call per ticket, shared by all cascades
                scout_cache[key] = timed(scout)(t.prompt)
            first, scout_s = scout_cache[key]
            t0 = time.time()
            out = scout_and_rescue(t.prompt, lambda p: first, rescue, lambda x: check(x, t), handoff=handoff)
            return Run(out.text, out.cost_usd, scout_s + time.time() - t0, out.path, check(out.text, t), out.rejected_because)
        return run

    def single(model):
        def run(t: Ticket) -> Run:
            result, s = timed(model)(t.prompt)
            return Run(result.text, result.cost_usd, s, "single", check(result.text, t))
        return run

    def scout_alone(t: Ticket) -> Run:
        """The cheap model with no rescuer: the same scout call the cascades use, kept even if a check fails.
        Compared with the baseline, it shows exactly what the rescuer adds."""
        key = id(t)
        if key not in scout_cache:
            scout_cache[key] = timed(scout)(t.prompt)
        first, scout_s = scout_cache[key]
        return Run(first.text, first.cost_usd, scout_s, "single", check(first.text, t))

    def cascade_with_policy_check(t: Ticket) -> Run:
        """Scout & Rescue where a reply must pass the code checks AND a policy check by a cheap model.
        The policy check's own cost is added to the run."""
        key = id(t)
        if key not in scout_cache:
            scout_cache[key] = timed(scout)(t.prompt)
        first, scout_s = scout_cache[key]
        extra = 0.0

        def both(x: str):
            nonlocal extra
            reason = check(x, t)
            if reason:
                return reason
            reason, cost = policy_check(t, x)
            extra += cost
            return reason

        t0 = time.time()
        out = scout_and_rescue(t.prompt, lambda p: first, opus_medium, both)
        final = both(out.text) if out.path == "rescue" else None
        return Run(out.text, out.cost_usd + extra, scout_s + time.time() - t0, out.path, final, out.rejected_because)

    with_policy = {"S&R + policy check (Haiku)": cascade_with_policy_check} if policy_check else {}
    return {
        "baseline (published)": cascade(opus_medium, handoff=False),
        **with_policy,
        "Haiku alone, no rescuer": scout_alone,
        "handoff": cascade(opus_medium, handoff=True),
        "rescuer effort low": cascade(opus_low, handoff=False),
        "Opus low, no scout": single(opus_low),
        "Opus medium, no scout": single(opus_medium),
    }


def stub_models():
    """Fake models so the wiring can be checked offline. Their numbers mean nothing."""
    def reply(model, cost, good):
        def call(prompt):
            t = next(x for x in TICKETS + HARD_TICKETS if f"Ticket:\n{x.text}" in prompt)
            cites = " ".join(f"({s})" for s in t.sections) if good or len(t.sections) == 1 else ""
            num = t.order_id or "order number"
            text = (f"Thanks for writing about {num}. We're sorry for the trouble and follow our policy {cites}. "
                    "A colleague will take over if needed and you'll hear from us by email soon. Kind regards.")
            return ModelResult(text, cost, model)
        return call

    judge = lambda p: ModelResult('{"policy_correct": 7, "solves": 7, "tone": 8, "clarity": 8, '
                                  '"hard_failure": false, "note": "stub"}', 0.0, "stub-judge")
    checker = lambda p: ModelResult('{"ok": ' + ('false' if 'audit' in p or 'Third' in p else 'true') + ', "problem": "stub"}',
                                    0.0002, "stub-checker")
    return (reply("stub-small", 0.0003, False), reply("stub-big", 0.0080, True), reply("stub-big-low", 0.0050, True),
            judge, checker, checker)


def live_models():
    from valueproof.claude import claude

    return (
        claude("claude-haiku-5-5", effort="low"),
        claude("claude-opus-5-5", effort="medium"),
        claude("claude-opus-5-5", effort="low"),
        claude("claude-opus-5-5", effort="medium"),  # judge
        claude("claude-haiku-5-5", effort="low"),    # policy check, cheap
        claude("claude-sonnet-5-5", effort="low"),   # policy check, mid-size (rated only)
    )


def build(live: bool, args: list[str]) -> dict:
    """Entry point for `valueproof compare examples/test_levers_support.py [--live] [--hard] [--setups "a|b"]`."""
    scout, opus_medium, opus_low, judge_model, check_haiku, check_sonnet = live_models() if live else stub_models()
    haiku_policy, sonnet_policy = make_policy_check(check_haiku), make_policy_check(check_sonnet)
    setups = build_setups(scout, opus_medium, opus_low, haiku_policy)

    def code_plus(policy):
        def fn(t, text):
            reason = check(text, t)
            return (reason, 0.0) if reason else policy(t, text)
        return fn

    # --rate-checks: try candidate eval checks on every reply of the run and rate them against the judge
    candidates = {
        "code checks (published)": lambda t, text: check(text, t),
        "code + policy check (Haiku)": code_plus(haiku_policy),
        "code + policy check (Sonnet)": code_plus(sonnet_policy),
    } if "--rate-checks" in args else None
    if "--setups" in args:  # e.g. --setups "baseline (published)|rescuer effort low"
        keep = args[args.index("--setups") + 1].split("|")
        setups = {name: setups[name] for name in keep if name in setups}  # the first one named is the baseline
    return {
        "cases": TICKETS + HARD_TICKETS if "--hard" in args else TICKETS,
        "setups": setups,
        "judge": make_judge(judge_model),
        "checks": candidates,
        "describe": lambda t: t.text,
    }


if __name__ == "__main__":
    from valueproof.cli import compare

    compare(__file__, live="--live" in sys.argv, extra=sys.argv[1:])
