import json
from pathlib import Path

# Defaults
DEBUG_FLAGS = {
    "GUI": False,
    "PROCESSING": False,
    "CALCULATION": False,
    "RENDERING": False,
}

# Try to read from debug.json in the current working directory
_debug_file = Path("debug.json")
if _debug_file.exists():
    try:
        with open(_debug_file, "r") as f:
            _user_flags = json.load(f)
            for _k, _v in _user_flags.items():
                if _k.upper() in DEBUG_FLAGS:
                    DEBUG_FLAGS[_k.upper()] = bool(_v)
    except Exception as e:
        print(f"Warning: Could not read {_debug_file}: {e}")

def set_debug_flag(category: str, value: bool):
    """Dynamically set a debug flag."""
    DEBUG_FLAGS[category.upper()] = value

def dprint(category: str, *args, **kwargs):
    """Print a debug message if the corresponding flag is true."""
    if DEBUG_FLAGS.get(category.upper(), False):
        print(f"[DEBUG - {category.upper()}]", *args, **kwargs)
