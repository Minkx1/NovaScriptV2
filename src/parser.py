"""
NovaScriptV2 - Parser
Made by Minkx1.
"""

from time import perf_counter
import typing

from .errors import NovaScriptError, ParserError
from .lexer import TokenType, Token, COMPARISONS


class ASTNode:
    ROOT: "ASTNode | None" = None

    def to_json(self) -> dict:
        raise NotImplementedError


class BlockStatement(ASTNode):  # {do1; do2; do3}
    def __init__(self, statements: list[ASTNode]):
        self.statements = statements

    def to_json(self):
        return {
            "type": "Block Statement",
            "body": [s.to_json() for s in self.statements],
        }


class AbstractSyntaxTree(BlockStatement):
    def __init__(self, statements: list[ASTNode]):
        super().__init__(statements)
        if ASTNode.ROOT:
            raise ParserError(
                "Unintentional behavior: More than 1 `AbstractSyntaxTree` ASTNodes were created."
            )

        ASTNode.ROOT = self

    def push_statements(self, *stmts: list[ASTNode]):
        self.statements.append([s for s in stmts])

    def to_json(self) -> dict:
        return {"type": "Program", "body": [s.to_json() for s in self.statements]}


class Literal(ASTNode):
    def __init__(self, type: typing.Literal["Number", "String", "Boolean"], value):
        self.type = type
        self.json = {}
        match self.type:
            case "Number":
                if isinstance(value, Token):
                    self.value = value.value
                elif isinstance(value, float | int):
                    self.value = value
                else:
                    raise ParserError("Unsupported LiteralNumber value type.")

                self.json = {"type": "Literal[Number]", "value": self.value}

            case "String":
                if isinstance(value, Token):
                    self.value = value.value
                elif isinstance(value, str):
                    self.value = value
                else:
                    raise ParserError("Unsupported LiteralString value type.")

                self.json = {"type": "Literal[String]", "value": self.value}

            case "Boolean":
                if isinstance(value, bool):
                    self.value = value
                else:
                    raise ParserError("Unsupported LiteralBoolean value type.")

                self.json = {"type": "Literal[Boolean]", "value": self.value}
            case _:
                raise ParserError(f"Unknown Literal type: {self.type}.")

    def to_json(self):
        return self.json


class Identifier(ASTNode):
    def __init__(self, value: Token):
        if isinstance(value, Token):
            self.value = value.value
        else:
            raise ParserError("Unsupported Identifier value type.")

    def to_json(self):
        return {"type": "Identifier", "value": self.value}


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


class BinOp(ASTNode):
    """+, -, *, /, %"""

    def __init__(self, left: ASTNode, op: Token, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right

    def to_json(self):
        return {
            "type": "Binary Expression",
            "operator": self.op.value,
            "left": self.left.to_json(),
            "right": self.right.to_json(),
        }


class BoolOp(ASTNode):
    def __init__(
        self, op1: ASTNode, operation: Token, op2: ASTNode
    ):
        self.op1 = op1
        self.op2 = op2
        self.operation = operation.value

    def to_json(self):
        return {
            "type": "Boolean Expression",
            "Expression": {
                "Operation": self.operation,
                "Operand1": self.op1.to_json(),
                "Opernad2": self.op2.to_json(),
            },
        }


class Call(ASTNode):
    def __init__(self, name, args: list[ASTNode], keywords_args: dict[str, ASTNode]):
        super().__init__()
        self.name = name
        self.args = args
        self.kwargs = keywords_args

    def to_json(self):
        return {
            "type": "Function Call",
            "name": self.name,
            "args": [a.to_json() for a in self.args],
            "kwargs": {k: v.to_json() for k, v in self.kwargs.items()},
        }


class IfStatement(ASTNode):
    def __init__(
        self,
        if_condition: BoolOp,
        if_body: BlockStatement,
        elif_statements: dict[BoolOp, BlockStatement] = {},
        else_body: BlockStatement = None,
    ):
        self.condition: BoolOp = if_condition
        self.body: BlockStatement = if_body
        self.elif_dict: dict[BoolOp, BlockStatement] = elif_statements
        self.else_body: BlockStatement = else_body

    def to_json(self):
        j = {
            "type": "If Statement",
            "If": {
                "condition": self.condition.to_json(),
                "body": self.body.to_json(),
            },
        }
        if self.elif_dict:
            j["Elif"] = [
                {"condition": c.to_json(), "body": b.to_json()}
                for c, b in self.elif_dict.items()
            ]
        if self.else_body:
            j["Else"] = self.else_body.to_json()

        return j


class WhileStatement(ASTNode):
    def __init__(self, condition: BoolOp, body: BlockStatement):
        self.condition = condition
        self.body = body

    def to_json(self):
        return {
            "type": "While Statement",
            "condition": self.condition.to_json(),
            "body": self.body.to_json(),
        }


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self._pos = 0
        self.semicolon = True

        self.start_t = perf_counter()
        self.time = 0

        self.AST = None

    @property
    def cur_tok(self):
        return (
            self.tokens[self._pos] if self._pos < len(self.tokens) else self.tokens[-1]
        )

    def peek_tok(self, step=1):
        if self._pos + step < len(self.tokens):
            return self.tokens[self._pos + step]
        else:
            raise EOFError

    def advance(self, step=1):
        self._pos += step
        return self.cur_tok

    def expect(self, *tok_types: TokenType):
        if self.cur_tok.type in tok_types:
            t = self.cur_tok
            self.advance()
            return t
        raise ParserError(
            f"Expected {[t.name for t in tok_types]}, got {self.cur_tok.type.name} at {self.cur_tok.pos}"
        )

    # --- MAIN ENTER POINT ---
    def parse_program(self) -> AbstractSyntaxTree:
        """Main entrypoint of parser, that builds AST from program and returns it."""
        self.statements = []
        while self.cur_tok.type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                self.statements.append(stmt)

        self.time = perf_counter() - self.start_t
        self.AST = AbstractSyntaxTree(self.statements)

        return self.AST

    def parse_statement(self) -> ASTNode:
        """Method is used to parse statements - main instructions.
        Statements are `Assignments`, `Function calls`, `If statements` etc.
        """
        stmt = None
        tok = self.cur_tok

        if tok.type == TokenType.IF:
            return self.parse_if()

        elif tok.type == TokenType.WHILE:
            return self.parse_while()

        elif tok.type == TokenType.IDENTIFIER:
            stmt = self.parse_identifier()

        # elif ...: ...

        self.expect(
            TokenType.SEMICOLON
        )  # If the ; is musthave to parse statements, like in C
        # elif tok.type == TokenType.SEMICOLON:         # If the ; is separator for statements, like in Python
        #     self.advance()
        #     return stmt
        return stmt

    # ADDITIONAL

    def parse_identifier(self) -> Identifier | Assign | Call:
        id_node = Identifier(self.cur_tok)
        self.advance()

        # Call
        if self.cur_tok.type == TokenType.LPAREN:
            return self.parse_call(id_node.value)
        # Assignment
        elif self.cur_tok.type == TokenType.ASSIGN:
            self.advance()
            value = self.parse_expression()
            expr = Assign(id_node, value)
            return expr

        return id_node

    def parse_if(self) -> IfStatement:
        self.advance()  # skip 'if'

        self.expect(TokenType.LPAREN)  # the `(condition)` must be put in paren-s
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)

        body = self.parse_block_statement()

        elifs = {}
        else_body = None

        while self.cur_tok.type == TokenType.ELIF:
            self.advance()

            self.expect(TokenType.LPAREN)
            elif_cond = self.parse_expression()
            self.expect(TokenType.RPAREN)

            elif_body = self.parse_block_statement()

            elifs[elif_cond] = elif_body

        if self.cur_tok.type == TokenType.ELSE:
            self.advance()

            else_body = self.parse_block_statement()

        stmt = IfStatement(condition, body, elifs, else_body)
        return stmt

    def parse_while(self) -> WhileStatement:
        self.advance()  # skip 'while'

        self.expect(TokenType.LPAREN)  # the `(condition)` must be put in paren-s
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)

        body = self.parse_block_statement()

        return WhileStatement(condition, body)

    def parse_call(self, name) -> Call:
        self.expect(TokenType.LPAREN)
        args = []
        kwargs = {}
        while self.cur_tok.type != TokenType.RPAREN:
            arg = self.parse_expression()
            # Keyword
            if isinstance(arg, Identifier) and self.cur_tok.type == TokenType.ASSIGN:
                self.advance()
                val = self.parse_expression()
                kwargs[arg.value] = val
            else:
                args.append(arg)

            if self.cur_tok.type == TokenType.COMMA:
                self.advance()
        self.expect(TokenType.RPAREN)
        return Call(name, args, kwargs)

    def parse_block_statement(self) -> BlockStatement:
        self.expect(TokenType.LBRACE)
        stmts = []
        while (
            self.cur_tok.type != TokenType.RBRACE and self.cur_tok.type != TokenType.EOF
        ):
            s = self.parse_statement()
            stmts.append(s)
        self.expect(TokenType.RBRACE)
        return BlockStatement(stmts)

    """ === EXPRESSIONS === """

    def parse_expression(self) -> None | ASTNode:
        """Expressions are methematical or boolean expression like `a + b` or `a != b`."""
        return (
            self.parse_comparison_expr()
        )  # Comparisons like '==' and '&&' have the least priority

    def parse_comparison_expr(self) -> None | ASTNode:
        left = self.parse_additive_expr()
        while self.cur_tok.type in COMPARISONS:
            op = self.cur_tok
            self.advance()
            right = self.parse_expression()
            left = BoolOp(left, op, right)
        return left

    def parse_additive_expr(self) -> None | ASTNode:
        left = self.parse_term_expr()
        while self.cur_tok.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.cur_tok
            self.advance()
            right = self.parse_term_expr()
            left = BinOp(left, op, right)
        return left

    def parse_term_expr(self) -> None | ASTNode:
        left = self.parse_factor_expr()
        while self.cur_tok.type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.cur_tok
            self.advance()
            right = self.parse_factor_expr()
            left = BinOp(left, op, right)
        return left

    def parse_factor_expr(self) -> None | ASTNode:
        left = self.parse_primary_expr()
        while self.cur_tok.type == TokenType.POWER:
            op = self.cur_tok
            self.advance()
            right = self.parse_primary_expr()
            left = BinOp(left, op, right)
        return left

    def parse_primary_expr(self) -> None | ASTNode:
        tok = self.cur_tok

        if tok.type == TokenType.NUMBER:
            self.advance()
            return Literal("Number", tok)
        elif tok.type == TokenType.STRING:
            self.advance()
            return Literal("String", tok)
        elif tok.type in (TokenType.TRUE, TokenType.FALSE):
            val = tok.type == TokenType.TRUE
            self.advance()
            return Literal("Boolean", val)

        elif tok.type == TokenType.IDENTIFIER:
            return self.parse_identifier()

        elif tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        # elif tok.type == TokenType.SEMICOLON: # SEMICOLON впринципі не має попасти в експрешн.
        #     return
        else:
            raise ParserError(
                f"Unexpected token in expression: {tok.type} at {tok.pos}"
            )


# EOF
