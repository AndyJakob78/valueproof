# Sample code

Small Python (3.10+) files you can copy into your own project. Only the Claude adapter needs a package (`anthropic`).

| File | What it is |
|---|---|
| [scout_rescue.py](scout_rescue.py) | The Scout & Rescue pattern in ~40 lines. Provider-neutral: a model is any function `prompt -> ModelResult`. |
| [pipeline.py](pipeline.py) | Split a job into steps and give each step its own model, or Scout & Rescue. Logs path and cost per step. |
| [claude_models.py](claude_models.py) | Adapter for Claude models (Haiku, Sonnet, Opus) with a simple cost estimate. Write a function with the same shape to use OpenAI, Gemini or a local model. |
| [demo_support.py](demo_support.py) | Worked example: support tickets. Cheap model reads the ticket, Scout & Rescue drafts the reply, mid-size model summarizes the batch. |
| [lever_runner.py](lever_runner.py) | Test one change against your current setup on the same requests, at the same time. Prints cost (average and median), rescue rate, time, check failures and blind-review quality, and writes a blind review sheet you can score by hand. |
| [test_levers_support.py](test_levers_support.py) | The [support test](../docs/support-test.md): Scout & Rescue vs. the strong model alone on 40 tickets, plus two levers (rescuer at low effort, handoff). |

## Run the demo

Without an API key (stub models, made-up costs, no charges):

```bash
python examples/demo_support.py
```

Against Claude (real calls, a few cents):

```bash
pip install anthropic
python examples/demo_support.py --live
```

Expected output (stub mode): two tickets finish on the cheap model; the hard billing ticket fails the reply check ("too short") and is rescued by the strong model.

## Test a lever

```bash
python examples/test_levers_support.py                 # stub models, checks the wiring, no cost
python examples/test_levers_support.py --live --hard   # real calls, about $2-3
```

Results go to `examples/results/<time>/`: `results.json`, plus `blind_review.csv` and `blind_key.csv` if you want to score the replies yourself. To test your own feature, copy the file and replace the policy, tickets, checks and setups. Expect Scout & Rescue to cost much less and lose a little quality — measure how much on your own requests. [Our results](../docs/support-test.md).

`scout_and_rescue(..., handoff=True)` also gives the rescuer the rejected draft and the reason. In our test it cost 12% more for no gain, so it is off by default.

## Make it yours

1. **Write the checks first.** What makes a result unusable, in code? Empty, invalid JSON, missing field, wrong id, too old, too short.
2. **Pick models per step.** Start cheap everywhere; let the checks show where you need the strong model.
3. **Log `path` and `cost_usd`.** How often the rescuer runs is your main cost driver over time.
4. **Prove it.** Compare against your current setup with a blind review before you ship — see the [method](../docs/method.md).
