"""Old name of `valueproof`. Kept so existing code keeps working; removed in version 1.0.

    import mixed_model_cost              ->  import valueproof
    from mixed_model_cost.claude import  ->  from valueproof.claude import
"""
import importlib
import sys
import warnings

warnings.warn(
    "`mixed_model_cost` is now `valueproof` - use `import valueproof`. The old name will be removed in version 1.0.",
    DeprecationWarning,
    stacklevel=2,
)

from valueproof import *  # noqa: E402,F401,F403
from valueproof import __all__, __version__  # noqa: E402,F401

# Old submodule paths: mixed_model_cost.claude, .openai, .gemini, ... point to valueproof's.
# Adapters import their provider SDK only when called, so this needs no extra packages.
for _name in ("scout_rescue", "pipeline", "lever_runner", "cli", "starter", "claude", "openai", "gemini"):
    sys.modules[f"{__name__}.{_name}"] = importlib.import_module(f"valueproof.{_name}")
