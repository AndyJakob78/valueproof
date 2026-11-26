# Sample code

Small Python (3.10+) files you can copy into your own project. Only the Claude adapter needs a package (`anthropic`).

| File | What it is |
|---|---|
| [scout_rescue.py](scout_rescue.py) | The Scout & Rescue pattern in ~40 lines. Provider-neutral: a model is any function `prompt -> ModelResult`. |
| [pipeline.py](pipeline.py) | Split a job into steps and give each step its own model, or Scout & Rescue. Logs path and cost per step. |
| [claude_models.py](claude_models.py) | Adapter for Claude models (Haiku, Sonnet, Opus) with a simple cost estimate. Write a function with the same shape to use OpenAI, Gemini or a local model. |
| [demo_support.py](demo_support.py) | Worked example: support tickets. Cheap model reads the ticket, Scout & Rescue drafts the reply, mid-size model summarizes the batch. |

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

## Make it yours

1. **Write the checks first.** What makes a result unusable, in code? Empty, invalid JSON, missing field, wrong id, too old, too short.
2. **Pick models per step.** Start cheap everywhere; let the checks show where you need the strong model.
3. **Log `path` and `cost_usd`.** How often the rescuer runs is your main cost driver over time.
4. **Prove it.** Compare against your current setup with a blind review before you ship — see the [method](../docs/method.md).
