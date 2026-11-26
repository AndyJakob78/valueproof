# Package and examples

Python 3.10+. Early version (0.1): the API may still change.

```bash
pip install "ai-mixed-model-cost-optimization[claude] @ git+https://github.com/AndyJakob78/ai-mixed-model-cost-optimization"
```

Leave out `[claude]` if you use another provider — the core has no dependencies. The examples also run straight from a clone without installing.

## What's in the package (`src/mixed_model_cost/`)

| Module | What it is |
|---|---|
| [scout_rescue.py](../src/mixed_model_cost/scout_rescue.py) | The Scout & Rescue pattern in ~40 lines. Provider-neutral: a model is any function `prompt -> ModelResult`. |
| [pipeline.py](../src/mixed_model_cost/pipeline.py) | Split a job into steps and give each step its own model, or Scout & Rescue. Logs path and cost per step. |
| [lever_runner.py](../src/mixed_model_cost/lever_runner.py) | Run every setup on every request, side by side, in a shuffled order. Prints cost (average and median), rescue rate, time, check failures and blind-review quality, and writes a blind review sheet you can score by hand. |
| [cli.py](../src/mixed_model_cost/cli.py) | The `mmco compare` command. |
| [claude.py](../src/mixed_model_cost/claude.py) | Adapter for Claude models (Haiku, Sonnet, Opus) with a simple cost estimate. |

**Other providers:** write a function with the same shape — prompt in, `ModelResult(text, cost_usd, model)` out — for OpenAI, Gemini or a local model. Everything else works unchanged.

## Examples (this folder)

| File | What it is |
|---|---|
| [demo_support.py](demo_support.py) | Support tickets: a cheap model reads the ticket, Scout & Rescue drafts the reply, a mid-size model summarizes the batch. |
| [test_levers_support.py](test_levers_support.py) | The [support test](../docs/support-test.md): Scout & Rescue vs. the strong model alone on 40 tickets, plus two levers (rescuer at low effort, handoff). A template for your own test. |

```bash
python examples/demo_support.py            # stub models, made-up costs, no charges
python examples/demo_support.py --live     # real Claude calls, a few cents
```

Expected output (stub mode): two tickets finish on the cheap model; the hard billing ticket fails the reply check ("too short") and is rescued by the strong model.

## Test a change on your own requests

```bash
mmco compare examples/test_levers_support.py               # stub models, checks the wiring, no cost
mmco compare examples/test_levers_support.py --live --hard # real calls, about $2-3
```

Your own test is one Python file with a `build` function:

```python
def build(live: bool, args: list[str]) -> dict:
    return {
        "cases":  my_requests,                           # 20-100 real requests, including hard ones
        "setups": {"today": run_today, "new": run_new},  # name -> run(case) -> Run; first is the baseline
        "judge":  my_judge,                              # optional: judge(case, text) -> Score, blind
    }
```

Results go to `results/<time>/` next to your file: `results.json`, plus `blind_review.csv` and `blind_key.csv` to score replies yourself. Copy [test_levers_support.py](test_levers_support.py) and replace the policy, tickets, checks and setups.

Expect Scout & Rescue to cost much less and lose a little quality — measure how much on your own requests. [Our results](../docs/support-test.md).

`scout_and_rescue(..., handoff=True)` also gives the rescuer the rejected draft and the reason. In our test it cost 12% more for no gain, so it is off by default.

## Make it yours

1. **Write the checks first.** What makes a result unusable, in code? Empty, invalid JSON, missing field, wrong id, too old, too short — and the costly mistakes for your domain.
2. **Pick models per step.** Start cheap everywhere; let the checks show where you need the strong model.
3. **Log `path` and `cost_usd`.** How often the rescuer runs is your main cost driver over time.
4. **Prove it** with `mmco compare` before you ship — see the [method](../docs/method.md).
