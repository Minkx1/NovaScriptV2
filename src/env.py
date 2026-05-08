"""
NovaScriptV2 - Environment.
by Minkx1.
"""
# This file contains environment for NovaScriptV2

ENV = {
    # built-in functions
    "print": print,
    "input": input,
    "to_int": int.__call__,
    "to_float": float.__call__,
    "to_str": str.__call__,
    "len": len,

    "__version__": "2.0.3"
}