from enum import Enum, auto
from typing import Any, Optional

from .errors import NovaScriptError, LexerError


class TokenType(Enum):
    """Token types for NovaScript lexer"""
    # Literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # Keywords
    __STDOUT__ = auto()

    # Operators
    ASSIGN = auto()       # =
    PLUS = auto()         # +
    MINUS = auto()        # -
    STAR = auto()         # *
    SLASH = auto()        # /
    PERCENT = auto()      # %
    POWER = auto()        # **

    # Comparison
    EQ = auto()           # ==
    NE = auto()           # !=
    LT = auto()           # <
    LE = auto()           # <=
    GT = auto()           # >
    GE = auto()           # >=
    
    # Delimiters
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    COMMA = auto()        # ,
    DOT = auto()          # .
    COLON = auto()        # :
    SEMICOLON = auto()    # ;
    ARROW = auto()        # ->

    # Special
    EOF = auto()

    KEYWORDS = {
        "__stdout__": __STDOUT__,
    }


class Token:
    """Represents a single token"""
    def __init__(self, type: TokenType, value: Any):
        self.type = type
        self.value = value

    def __repr__(self) -> str:
        return f"Token< {self.type.name} :: {self.value} >"

    def __str__(self) -> str:
        return self.__repr__()


class Lexer:
    def __init__(self, src_code: list[str]):
        self.code = src_code
        self.line = 0
        self.char = 0
        self.tokens: list[Token] = []
        self.eof = False

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
            return '\0'
        
        if self.char < len(self.code[self.line]) - 1:
            return self.code[self.line][self.char + 1]
        else:
            # Виправлено: забрали -1
            if self.line + 1 < len(self.code): 
                return self.code[self.line + 1][0]
            else:
                return '\0'
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

    def skip_whitespace(self):
        while self.cur_char() in " \t\n":
            self.advance()
    def skip_comments(self):
        if self.cur_char() == "/" and self.peek_char() == "/":
            while self.cur_char() != "\n" and not self.eof:
                self.advance()
            self.advance() # пропускаємо сам \n після коментаря
        self.skip_whitespace()

    def parse_number(self) -> Token:
        num_s = ""
        has_dot = False
        
        while self.cur_char().isdigit() or self.cur_char() == '.':
            if self.cur_char() == '.':
                if has_dot: # Якщо крапка зустрічається вдруге (напр. 1.2.3)
                    self.error("Invalid number format")
                has_dot = True
            
            num_s += self.cur_char()
            self.advance()
            
        num = float(num_s) if has_dot else int(num_s)
        return Token(TokenType.NUMBER, num)
    def parse_identifier(self) -> Token:
        identifier = ""
        
        while self.cur_char().isalnum() or self.cur_char() == '_':
            identifier += self.cur_char()
            self.advance()
            
        t_type = TokenType.KEYWORDS.value.get(identifier, TokenType.IDENTIFIER)
        return Token(t_type, identifier)
    def parse_operators(self) -> Token:
        char = self.cur_char()
        
        if char == '+':
            if self.peek_char() == '=':
                self.advance()
                self.advance()
                return Token(TokenType.PLUS_ASSIGN, '+=')
            self.advance()
            return Token(TokenType.PLUS, '+')
        
        elif char == '-':
            if self.peek_char() == '=':
                self.advance()
                self.advance()
                return Token(TokenType.MINUS_ASSIGN, '-=')
            elif self.peek_char() == '>':
                self.advance()
                self.advance()
                return Token(TokenType.ARROW, '->')
            self.advance()
            return Token(TokenType.MINUS, '-')
        
        elif char == '*':
            if self.peek_char() == '*':
                self.advance()
                self.advance()
                return Token(TokenType.POWER, '**')
            self.advance()
            return Token(TokenType.STAR, '*')
        
        elif char == '/':
            self.advance()
            return Token(TokenType.SLASH, '/')
        
        elif char == '%':
            self.advance()
            return Token(TokenType.PERCENT, '%')
        
        elif char == '=':
            if self.peek_char() == '=':
                self.advance()
                self.advance()
                return Token(TokenType.EQ, '==')
            self.advance()
            return Token(TokenType.ASSIGN, '=')
        
        elif char == '!':
            if self.peek_char() == '=':
                self.advance()
                self.advance()
                return Token(TokenType.NE, '!=')
            self.error(f"Unexpected character: {char}")
        
        elif char == '<':
            if self.peek_char() == '=':
                self.advance()
                self.advance()
                return Token(TokenType.LE, '<=')
            self.advance()
            return Token(TokenType.LT, '<')
        
        elif char == '>':
            if self.peek_char() == '=':
                self.advance()
                self.advance()
                return Token(TokenType.GE, '>=')
            self.advance()
            return Token(TokenType.GT, '>')
        
        elif char == '(':
            self.advance()
            return Token(TokenType.LPAREN, '(')
        elif char == ')':
            self.advance()
            return Token(TokenType.RPAREN, ')')
        elif char == '{':
            self.advance()
            return Token(TokenType.LBRACE, '{')
        elif char == '}':
            self.advance()
            return Token(TokenType.RBRACE, '}')
        elif char == '[':
            self.advance()
            return Token(TokenType.LBRACKET, '[')
        elif char == ']':
            self.advance()
            return Token(TokenType.RBRACKET, ']')
        elif char == ',':
            self.advance()
            return Token(TokenType.COMMA, ',')
        elif char == '.':
            self.advance()
            return Token(TokenType.DOT, '.')
        elif char == ':':
            self.advance()
            return Token(TokenType.COLON, ':')
        elif char == ';':
            self.advance()
            return Token(TokenType.SEMICOLON, ';')
        else:
            self.error(f"Unexpected character: {char}")

    def tokenize(self) -> list[Token]:
        while not self.eof:
            self.skip_whitespace()
            self.skip_comments()

            char = self.cur_char()
            
            if char == '\0' or self.eof:
                self.push_token(Token(TokenType.EOF, '\\0'))
                break

            if char.isdigit() or char == '.':
                self.push_token(self.parse_number())
            elif char.isalpha() or char == '_':
                self.push_token(self.parse_identifier())
            else:
                self.push_token(self.parse_operators())

        return self.tokens