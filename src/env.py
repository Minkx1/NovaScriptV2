"""
NovaScriptV2 - Environment.
by Minkx1.
"""
# This file contains environment for NovaScriptV2

ENV = {
    "println": print,
    "getln": input,
    "to_int": int.__call__,
    "to_float": float.__call__,
    "to_str": str.__call__,
    "__version__": "2.0.1"
}