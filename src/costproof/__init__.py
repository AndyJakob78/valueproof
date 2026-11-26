"""Costproof: let cheap and strong models work together,
and measure what each change does to cost and quality before it ships.

    from costproof import scout_and_rescue, ModelResult
    from costproof.claude import claude              # [claude] extra
    from costproof.openai import openai_model        # [openai] extra
    from costproof.gemini import gemini_model        # [gemini] extra

Any provider works: a model is just a function `prompt -> ModelResult`.
"""

from .lever_runner import Report, Run, Score, is_outcome, print_table, run_levers, save, summarize
from .pipeline import RunResult, Step, StepLog, run_pipeline
from .scout_rescue import Check, Model, ModelResult, Outcome, handoff_prompt, scout_and_rescue

__version__ = "0.4.0"

__all__ = [
    "Check", "Model", "ModelResult", "Outcome", "handoff_prompt", "scout_and_rescue",
    "RunResult", "Step", "StepLog", "run_pipeline",
    "Report", "Run", "Score", "is_outcome", "print_table", "run_levers", "save", "summarize",
]
