"""
NovaScriptV2 - Parser
Made by Minkx1.
"""

from time import perf_counter

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
    
class Call(ASTNode):
    def __init__(self, name, args:list[ASTNode], keywords_args:dict[str, ASTNode]):
        super().__init__()
        self.name = name
        self.args = args
        self.kwargs = keywords_args

    def to_json(self):
        return {"type": "Function-Call", "name": self.name, "args": [a.to_json() for a in self.args], "kwargs": {k: v.to_json() for k, v in self.kwargs.items()},}

class Identifier(ASTNode):
    def __init__(self, value: Token):
        if isinstance(value, Token):
            self.value = value.value
        else:
            raise ParserError("Unsupported Identifier value type.")

    def to_json(self):
        return {"type": "Identifier", "value": self.value}

class LiteralNumber(ASTNode):
    def __init__(self, value: float | int | Token):
        if isinstance(value, Token):
            self.value = value.value
        elif isinstance(value, float | int):
            self.value = value
        else:
            raise ParserError("Unsupported LiteralNumber value type.")

    def to_json(self):
        return {"type": "LiteralNumber", "value": self.value}

class LiteralString(ASTNode):
    def __init__(self, value: str | Token):
        if isinstance(value, Token):
            self.value = value.value
        elif isinstance(value, str):
            self.value = value
        else:
            raise ParserError("Unsupported LiteralString value type.")

    def to_json(self):
        return {"type": "LiteralString", "value": self.value}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.AST = None
        self._pos = 0

        self.start_t = perf_counter()
        self.time = 0

    @property
    def cur_tok(self):
        return self.tokens[self._pos]
    
    def peek_tok(self, step=1):
        if self._pos + step < len(self.tokens):
            return self.tokens[self._pos + step]
        else:
            raise EOFError
    
    def advance(self, step=1):
        if self._pos + step < len(self.tokens):
            self._pos += step
        else:
            raise EOFError
    
    def expect(self, tok_type: TokenType):
        if self.cur_tok.type == tok_type:
            self.advance()
        else:
            raise ParserError(f"Expected {tok_type.name}, instead got {self.cur_tok.type.name} at position {self.cur_tok.pos}")


    def parse_program(self) -> AbstractSyntaxTree:
        statements = []

        while self.cur_tok.type != TokenType.EOF:
            st: ASTNode | None = self.parse_expression()
            if st is not None:
                self.expect(TokenType.SEMICOLON)
                statements.append(st)

        self.AST = AbstractSyntaxTree(statements)
        self.time = perf_counter() - self.start_t
        return self.AST

    def parse_standart_case(self) -> None:
        # cur_tok.type == _
        raise ParserError(f"Unexpected token: {self.cur_tok}") 

    def parse_eof(self) -> None:
        # cur_tok.type == EOF
        return None

    def parse_semicolon(self) -> None:
        # cur_tok.type == ;
        raise ParserError(f"Unexpected ; at {self.cur_tok.pos}.")

    def parse_call(self) -> None|ASTNode:
        name = self.cur_tok.value # call token = call name
        args = []
        kwargs = {}

        self.advance()
        self.expect(TokenType.LPAREN)

        while(self.cur_tok.type != TokenType.RPAREN):
            # f(id1, op1+op2, arg1=id2, arg2 = op1+op2) 
            if self.cur_tok.type == TokenType.COMMA:
                self.advance()
                continue
            else:
                expr = self.parse_expression()
                if expr.__class__ == Assign:
                    key = expr.target.value
                    value = expr.value
                    kwargs[key] = value
                else:
                    args.append(expr)

        self.expect(TokenType.RPAREN)
        return Call(name, args, kwargs)

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
        """Рівень 4: Базові типи та ДУЖКИ"""
        tok = self.cur_tok
        
        if tok.type == TokenType.EOF:
            return self.parse_eof()
        
        elif tok.type == TokenType.SEMICOLON:
            return self.parse_semicolon()
        
        elif tok.type == TokenType.NUMBER:
            self.advance()
            return LiteralNumber(tok)
            
        elif tok.type == TokenType.STRING:
            self.advance()
            return LiteralString(tok)
            
        elif tok.type == TokenType.IDENTIFIER:
            if self.peek_tok().type == TokenType.LPAREN:
                return self.parse_call()
            elif self.peek_tok().type == TokenType.ASSIGN:
                return self.parse_assign()
            else:
                id = Identifier(tok)
                self.advance()
                return id
            
        elif tok.type == TokenType.LPAREN:
            self.advance() # Пропускаємо ліву дужку '('
            expr = self.parse_expression() # РЕКУРСІЯ! Парсимо все, що всередині
            self.expect(TokenType.RPAREN)  # Вимагаємо праву дужку ')'
            return expr
        else:
            raise ParserError(f"Unexpected token in expression: {tok.type.name} at {tok.line}:{tok.col}")
