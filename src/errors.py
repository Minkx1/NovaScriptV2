"""
NovaScriptV2 - Errors
Made by Minkx1.
"""


class NovaScriptError(Exception): ...


class LexerError(NovaScriptError): ...


class ParserError(NovaScriptError): ...


class NovaValidatorError(NovaScriptError): ...


class SyntaxError(NovaScriptError): ...


class GeneratorError(NovaScriptError): ...


class NovaCompilerError(NovaScriptError): ...
