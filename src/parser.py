"""
NovaScriptV2 - Parser
Made by Minkx1.
"""

from .errors import NovaScriptError, ParserError
from .lexer import TokenType, Token


class ASTNode:
    ROOT: "ASTNode | None" = None

    def to_json(self) -> dict:
        raise NotImplementedError()

class AbstractSyntaxTree(ASTNode):
    def __init__(self, statements: list[ASTNode]):
        super().__init__()
        self.statements = statements
        if ASTNode.ROOT:
            raise ParserError(
                "Unintentional behavior: More than 1 `AbstractSyntaxTree` ASTNodes were created."
            )

        ASTNode.ROOT = self

    def push_statements(self, *stmts: list[ASTNode]):
        self.statements.append([s for s in stmts])

    def to_json(self) -> dict:
        return {"type": "Program", "body": [s.to_json() for s in self.statements]}


class BinOp(ASTNode):
    """+, -, *, /, %"""

    token_types = [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.STAR,
        TokenType.SLASH,
        TokenType.PERCENT,
        TokenType.POWER,
    ]

    def __init__(self, left: ASTNode, op: Token, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right

    def to_json(self):
        return {
            "type": "BinaryExpression",
            "operator": self.op.value,
            "left": self.left.to_json(),
            "right": self.right.to_json(),
        }

# class BoolOp(ASTNode):
#     """+, -, *, /, %"""

#     token_types = [
#     ]

#     def __init__(self, left: ASTNode, op: Token, right: ASTNode):
#         self.left = left
#         self.op = op
#         self.right = right

#     def to_json(self):
#         return {
#             "type": "BinaryExpression",
#             "operator": self.op.value,
#             "left": self.left.to_json(),
#             "right": self.right.to_json(),
#         }

class Assign(ASTNode):
    def __init__(self, target: "Identifier", value: ASTNode):
        self.target = target
        self.value = value

    def to_json(self):
        return {
            "type": "Assignment",
            "target": self.target.to_json(),
            "value": self.value.to_json(),
        }


class STDOUTCall(ASTNode):
    def __init__(self, statement:ASTNode):
        super().__init__()
        self.value = statement

    def to_json(self):
        return {"type": "STDOUT-call", "value": self.value.to_json()}

class Identifier(ASTNode):
    def __init__(self, value: Token):
        if isinstance(value, Token):
            self.value = value.value
        else:
            raise ParserError("Unsupported Identifier value type.")

    def to_json(self):
        return {"type": "Identifier", "value": self.value}

class Number(ASTNode):
    def __init__(self, value: float | int | Token):
        if isinstance(value, Token):
            self.value = value.value
        elif isinstance(value, float | int):
            self.value = value
        else:
            raise ParserError("Unsupported Number value type.")

    def to_json(self):
        return {"type": "LiteralNumber", "value": self.value}

class String(ASTNode):
    def __init__(self, value: str | Token):
        if isinstance(value, Token):
            self.value = value.value
        elif isinstance(value, str):
            self.value = value
        else:
            raise ParserError("Unsupported String value type.")

    def to_json(self):
        return {"type": "LiteralString", "value": self.value}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    @property
    def cur_tok(self):
        return self.tokens[self.pos]
    
    def peek_tok(self, step=1):
        if self.pos + step < len(self.tokens):
            return self.tokens[self.pos + step]
        else:
            raise EOFError
    
    def advance(self, step=1):
        if self.pos + step < len(self.tokens):
            self.pos += step
        else:
            raise EOFError
    
    def expect(self, tok_type: TokenType):
        if self.cur_tok.type == tok_type:
            self.advance()
        else:
            raise ParserError(f"Expected {tok_type.name}, instead got {self.cur_tok.type.name} at position {self.pos}")


    def parse_program(self) -> AbstractSyntaxTree:
        statements = []

        while self.cur_tok.type != TokenType.EOF:
            st: ASTNode | None = self.parse_statement()
            if st is not None:
                self.expect(TokenType.SEMICOLON)
                statements.append(st)

        return AbstractSyntaxTree(statements)

    def parse_statement(self) -> None | ASTNode:
        tok = self.cur_tok

        if tok.type == TokenType.EOF:
            return self.parse_eof()
        elif tok.type == TokenType.SEMICOLON:
            return self.parse_semicolon()
        elif tok.type == TokenType.STDOUT:
            return self.parse_stdout()
        elif tok.type == TokenType.IDENTIFIER and self.peek_tok(1).type == TokenType.ASSIGN:
            return self.parse_assign()
        else:
            return self.parse_expression()

    def parse_standart_case(self) -> None:
        # cur_tok.type == _
        raise ParserError(f"Unexpected token: {self.cur_tok}") 

    def parse_eof(self) -> None:
        # cur_tok.type == EOF
        return None

    def parse_semicolon(self) -> None:
        # cur_tok.type == ;
        raise ParserError(f"Unexpected ; at {self.pos}.")

    def parse_stdout(self) -> None|ASTNode:
        self.advance() # skipping stdout tok
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        return STDOUTCall(expr)

    def parse_assign(self) -> None|ASTNode:
        id_node = Identifier(self.cur_tok)
        self.advance(2)
        expr = self.parse_expression()
        return Assign(id_node, expr)

    def parse_expression(self) -> ASTNode:
        """Рівень 1: Додавання та віднімання (+, -)"""
        """ Рекурсивний виклик нижніх, більш пріорітетних рівнів, таких як множення, степінь, літерали та дужки"""
        left = self.parse_term()
        
        while self.cur_tok.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.cur_tok
            self.advance()
            right = self.parse_term()
            left = BinOp(left, op, right)
            
        return left

    def parse_term(self) -> ASTNode:
        """Рівень 2: Множення, ділення та остача (*, /, %)"""
        left = self.parse_factor()
        
        while self.cur_tok.type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.cur_tok
            self.advance()
            right = self.parse_factor()
            left = BinOp(left, op, right)
            
        return left

    def parse_factor(self) -> ASTNode:
        """Рівень 3: Степінь (**)"""
        left = self.parse_primary()
        
        while self.cur_tok.type == TokenType.POWER:
            op = self.cur_tok
            self.advance()
            right = self.parse_primary()
            left = BinOp(left, op, right)
            
        return left

    def parse_primary(self) -> ASTNode:
        """Рівень 4: Базові типи (Числа, Змінні, Рядки) та ДУЖКИ"""
        tok = self.cur_tok
        
        if tok.type == TokenType.NUMBER:
            self.advance()
            return Number(tok)
            
        elif tok.type == TokenType.STRING:
            self.advance()
            return String(tok)
            
        elif tok.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(tok)
            
        elif tok.type == TokenType.LPAREN:
            self.advance() # Пропускаємо ліву дужку '('
            expr = self.parse_expression() # РЕКУРСІЯ! Парсимо все, що всередині
            self.expect(TokenType.RPAREN)  # Вимагаємо праву дужку ')'
            return expr
            
        else:
            raise ParserError(f"Unexpected token in expression: {tok.type.name} at {self.pos}")
