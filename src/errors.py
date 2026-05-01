class NovaScriptError(Exception):
    pass


class LexerError(NovaScriptError):
    pass
class ParserError(NovaScriptError):
    pass
class SyntaxError(NovaScriptError):
    pass
class CompilerError(NovaScriptError):
    pass