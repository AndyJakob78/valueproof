from valueproof import ModelResult, Step, handoff_prompt, run_pipeline, scout_and_rescue


def model(name, cost, text):
    calls = []

    def call(prompt):
        calls.append(prompt)
        return ModelResult(text(prompt) if callable(text) else text, cost, name)

    call.calls = calls
    return call


def test_scout_passes_and_rescuer_never_runs():
    scout, rescue = model("cheap", 0.001, "good answer"), model("strong", 0.01, "strong answer")
    out = scout_and_rescue("q", scout, rescue, lambda t: None)
    assert (out.path, out.text, out.cost_usd, out.model) == ("scout", "good answer", 0.001, "cheap")
    assert rescue.calls == []


def test_rescue_pays_for_both_and_keeps_reason():
    scout, rescue = model("cheap", 0.001, "bad"), model("strong", 0.01, "fixed")
    out = scout_and_rescue("q", scout, rescue, lambda t: "too short" if t == "bad" else None)
    assert out.path == "rescue" and out.text == "fixed" and out.rejected_because == "too short"
    assert abs(out.cost_usd - 0.011) < 1e-12
    assert rescue.calls == ["q"]  # no handoff by default


def test_handoff_gives_rescuer_the_draft_and_reason():
    scout, rescue = model("cheap", 0, "bad draft"), model("strong", 0, "fixed")
    scout_and_rescue("q", scout, rescue, lambda t: "wrong id", handoff=True)
    assert rescue.calls == [handoff_prompt("q", "bad draft", "wrong id")]
    assert "wrong id" in rescue.calls[0] and "bad draft" in rescue.calls[0]


def test_pipeline_runs_steps_in_order_and_logs_cost():
    read = model("cheap", 0.001, "ID 42")
    reply_scout = model("cheap", 0.002, "short")
    reply_rescue = model("strong", 0.02, lambda p: "Your order 42 is on its way.")
    steps = [
        Step("read", lambda d: d["ticket"], model=read),
        Step("reply", lambda d: "reply to " + d["read"], scout=reply_scout, rescue=reply_rescue,
             check=lambda text, d: None if "42" in text else "no id"),
    ]
    run = run_pipeline(steps, {"ticket": "where is 42"})
    assert run.data["reply"] == "Your order 42 is on its way."
    assert [e.path for e in run.log] == ["single", "rescue"]
    assert abs(run.cost_usd - 0.023) < 1e-12
