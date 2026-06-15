"""
NovaScriptV2 - Lexer
Made by Minkx1.
"""

import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

from .errors import LexerError


class TokenType(Enum):
    """Token types for NovaScript lexer"""

    # Literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # Keywords
    IF = auto()
    ELSE = auto()
    ELIF = auto()
    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()

    IMPORT = auto()
    WHILE = auto()
    FOR = auto()

    TRY = auto()
    EXCEPT = auto()
    NOT = auto()  # !

    # Operators
    ASSIGN = auto()  # =
    PLUS = auto()  # +
    MINUS = auto()  # -
    PLUS_ASSIGN = auto()  # +=
    MINUS_ASSIGN = auto()  # -=
    STAR = auto()  # *
    SLASH = auto()  # /
    PERCENT = auto()  # %
    POWER = auto()  # **

    # Comparison
    EQ = auto()  # ==
    NE = auto()  # !=
    LT = auto()  # <
    LE = auto()  # <=
    GT = auto()  # >
    GE = auto()  # >=

    # Delimiters
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    COMMA = auto()  # ,
    DOT = auto()  # .
    COLON = auto()  # :
    SEMICOLON = auto()  # ;
    ARROW = auto()  # ->

    # Special
    EOF = auto()


KEYWORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "elif": TokenType.ELIF,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "or": TokenType.OR,
    "||": TokenType.OR,
    "and": TokenType.AND,
    "&&": TokenType.AND,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "try": TokenType.TRY,
    "except": TokenType.EXCEPT,
    "not": TokenType.NOT,
    "import": TokenType.IMPORT,
}

COMPARISONS = (
    TokenType.EQ,
    TokenType.NE,
    TokenType.LE,
    TokenType.LT,
    TokenType.GE,
    TokenType.GT,
)
BINARY_OP = (
    TokenType.PLUS,
    TokenType.MINUS,
    TokenType.STAR,
    TokenType.SLASH,
    TokenType.PERCENT,
    TokenType.POWER,
)


@dataclass
class Token:
    """Represents a single token"""

    type: TokenType
    value: Any
    line: int
    col: int

    def __post_init__(self):
        self.line += 1
        self.col += 1

    def __repr__(self) -> str:
        return f"T_{self.type.name} {self.value} : ({self.line}:{self.col})"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def pos(self) -> str:
        return f"{self.line}:{self.col}"


class Lexer:
    def __init__(self, src_code: str | list[str]):
        self.code = src_code.splitlines() if isinstance(src_code, str) else src_code
        self.line = 0
        self.char = 0
        self.tokens: list[Token] = []
        self.eof = False

        self.start_time = time.perf_counter()
        self.time = 0

    def error(self, message: str):
        raise LexerError(message)

    def push_token(self, token: Optional[Token]):
        if isinstance(token, Token):
            self.tokens.append(token)

    def cur_char(self):
        if self.eof or not self.code:
            return "\0"
        return self.code[self.line][self.char]

    def peek_char(self):
        if self.eof or not self.code:
            return "\0"

        if self.char + 1 < len(self.code[self.line]):
            return self.code[self.line][self.char + 1]

        next_line = self.line + 1
        while next_line < len(self.code) and self.code[next_line] == "":
            next_line += 1

        if next_line < len(self.code):
            return self.code[next_line][0]
        return "\0"

    def advance(self):
        if self.eof:
            return

        if self.char < len(self.code[self.line]) - 1:
            self.char += 1
        else:
            # Виправлено: забрали -1
            if self.line + 1 < len(self.code):
                self.char = 0
                self.line += 1
            else:
                self.eof = True

    def skip_ignored(self):
        while True:
            if self.cur_char() in " \t\n":
                self.advance()
                continue

            if self.cur_char() == "/":
                if self.peek_char() == "/":
                    while not self.eof and self.cur_char() != "\n":
                        if self.char == len(self.code[self.line]) - 1:
                            self.advance()
                            break
                        self.advance()
                    if self.cur_char() == "\n":
                        self.advance()  # skip "\n" after comment
                    continue
                if self.peek_char() == "*":
                    self.advance()
                    self.advance()
                    while not self.eof and not (
                        self.cur_char() == "*" and self.peek_char() == "/"
                    ):
                        self.advance()
                    if self.eof:
                        self.error("Unterminated comment")
                    self.advance()
                    self.advance()  # Skipping '*/'
                    continue

            break

    def parse_number(self) -> Token:
        num_s = ""
        start_line = self.line
        start_char = self.char

        if self.cur_char() == ".":
            num_s += "."
            self.advance()
            if not self.cur_char().isdigit():
                self.error("Invalid number format")
            while self.cur_char().isdigit():
                num_s += self.cur_char()
                self.advance()
        else:
            while self.cur_char().isdigit():
                num_s += self.cur_char()
                self.advance()
            if self.cur_char() == ".":
                num_s += "."
                self.advance()
                if not self.cur_char().isdigit():
                    self.error("Invalid number format")
                while self.cur_char().isdigit():
                    num_s += self.cur_char()
                    self.advance()

        if self.cur_char() == ".":
            self.error("Invalid number format")

        num = float(num_s) if "." in num_s else int(num_s)
        return Token(TokenType.NUMBER, num, start_line, start_char)

    def parse_string(self) -> Token:
        quote_char = self.cur_char()

        start_line = self.line
        start_col = self.char
        self.advance()  # Skip opening quote

        string_value = ""
        while self.cur_char() != quote_char and self.cur_char() != "\0":
            if self.cur_char() == "\\":
                self.advance()
                # Handle escape sequences
                escape_char = self.cur_char()
                if escape_char == "n":
                    string_value += "\n"
                elif escape_char == "t":
                    string_value += "\t"
                elif escape_char == "r":
                    string_value += "\r"
                elif escape_char == "\\":
                    string_value += "\\"
                elif escape_char == quote_char:
                    string_value += quote_char
                else:
                    string_value += escape_char
                self.advance()
            else:
                string_value += self.cur_char()
                self.advance()

        if self.cur_char() != quote_char:
            self.error(f"Unterminated string.")

        self.advance()  # Skip closing quote
        return Token(TokenType.STRING, string_value, start_line, start_col)

    def parse_identifier(self) -> Token:
        identifier = ""
        start_line = self.line
        start_char = self.char

        while self.cur_char().isalnum() or self.cur_char() == "_":
            identifier += self.cur_char()
            self.advance()

        t_type = KEYWORDS.get(identifier, TokenType.IDENTIFIER)
        if t_type == TokenType.TRUE:
            return Token(t_type, True, start_line, start_char)
        elif t_type == TokenType.FALSE:
            return Token(t_type, False, start_line, start_char)

        return Token(t_type, identifier, start_line, start_char)

    def parse_operators(self) -> Token:
        char = self.cur_char()
        start_line, start_char = self.line, self.char

        if char == "+":
            if self.peek_char() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.PLUS_ASSIGN, "+=", start_line, start_char)
            self.advance()
            return Token(TokenType.PLUS, "+", start_line, start_char)

        elif char == "-":
            if self.peek_char() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.MINUS_ASSIGN, "-=", start_line, start_char)
            elif self.peek_char() == ">":
                self.advance()
                self.advance()
                return Token(TokenType.ARROW, "->", start_line, start_char)
            self.advance()
            return Token(TokenType.MINUS, "-", start_line, start_char)

        elif char == "*":
            if self.peek_char() == "*":
                self.advance()
                self.advance()
                return Token(TokenType.POWER, "**", start_line, start_char)
            self.advance()
            return Token(TokenType.STAR, "*", start_line, start_char)

        elif char == "/":
            self.advance()
            return Token(TokenType.SLASH, "/", start_line, start_char)

        elif char == "%":
            self.advance()
            return Token(TokenType.PERCENT, "%", start_line, start_char)

        elif char == "=":
            if self.peek_char() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.EQ, "==", start_line, start_char)
            self.advance()
            return Token(TokenType.ASSIGN, "=", start_line, start_char)

        elif char == "!":
            if self.peek_char() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.NE, "!=", start_line, start_char)
            self.advance()
            return Token(TokenType.NOT, "!", start_line, start_char)

        elif char == "<":
            if self.peek_char() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.LE, "<=", start_line, start_char)
            self.advance()
            return Token(TokenType.LT, "<", start_line, start_char)

        elif char == ">":
            if self.peek_char() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.GE, ">=", start_line, start_char)
            self.advance()
            return Token(TokenType.GT, ">", start_line, start_char)

        elif char == "(":
            self.advance()
            return Token(TokenType.LPAREN, "(", start_line, start_char)
        elif char == ")":
            self.advance()
            return Token(TokenType.RPAREN, ")", start_line, start_char)
        elif char == "{":
            self.advance()
            return Token(TokenType.LBRACE, "{", start_line, start_char)
        elif char == "}":
            self.advance()
            return Token(TokenType.RBRACE, "}", start_line, start_char)
        elif char == "[":
            self.advance()
            return Token(TokenType.LBRACKET, "[", start_line, start_char)
        elif char == "]":
            self.advance()
            return Token(TokenType.RBRACKET, "]", start_line, start_char)
        elif char == ",":
            self.advance()
            return Token(TokenType.COMMA, ",", start_line, start_char)
        elif char == ".":
            self.advance()
            return Token(TokenType.DOT, ".", start_line, start_char)
        elif char == ":":
            self.advance()
            return Token(TokenType.COLON, ":", start_line, start_char)
        elif char == ";":
            self.advance()
            return Token(TokenType.SEMICOLON, ";", start_line, start_char)
        else:
            self.error(f"Unexpected character: {char}")

    def tokenize(self) -> list[Token]:
        while not self.eof:
            self.skip_ignored()

            char = self.cur_char()

            if char == "\0" or self.eof:
                # self.push_token(Token(TokenType.EOF, '\\0'), self.line, self.char)
                break

            if char.isdigit() or (char == "." and self.peek_char().isdigit()):
                self.push_token(self.parse_number())
            elif char == '"' or char == "'":
                self.push_token(self.parse_string())
            elif char.isalpha() or char == "_":
                self.push_token(self.parse_identifier())
            else:
                self.push_token(self.parse_operators())

        if not self.tokens or self.tokens[-1].type != TokenType.EOF:
            self.push_token(Token(TokenType.EOF, "\0", self.line, self.char))

        self.time = time.perf_counter() - self.start_time
        return self.tokens

    def serialize(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            for token in self.tokens:
                f.write(f"{token}\n")

    @staticmethod
    def deserialize(path: str):
        with open(path, "r", encoding="utf-8") as f:
            tokens = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Example: T_IDENTIFIER myVar : (1:5)
                try:
                    type_part, rest = line.split(" ", 1)
                    value_part, pos_part = rest.rsplit(" : ", 1)
                    type_name = type_part[2:]
                    token_type = TokenType[type_name]
                    value = eval(value_part)  # Осторожно! eval может быть опасен
                    line_num, col_num = map(int, pos_part.strip("()").split(":"))
                    tokens.append(Token(token_type, value, line_num, col_num))
                except Exception as e:
                    raise LexerError(
                        f"Failed to deserialize token from line: {line}"
                    ) from e

        return tokens
