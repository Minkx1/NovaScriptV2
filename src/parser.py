"""
NovaScriptV2 - Parser
Made by Minkx1.
"""

from dataclasses import dataclass, field
from time import perf_counter
from typing import Literal as LiteralType

from .errors import ParserError
from .lexer import TokenType, Token, COMPARISONS


class ASTNode:
    ROOT: "ASTNode | None" = None

    def to_json(self) -> dict:
        raise NotImplementedError


@dataclass
class BlockStatement(ASTNode):  # {do1; do2; do3}
    statements: list[ASTNode]

    def to_json(self):
        return {
            "type": "Block Statement",
            "body": [s.to_json() for s in self.statements],
        }


@dataclass
class AbstractSyntaxTree(BlockStatement):
    def __post_init__(self):
        if ASTNode.ROOT:
            raise ParserError(
                "Unintentional behavior: More than 1 `AbstractSyntaxTree` ASTNodes were created."
            )

        ASTNode.ROOT = self

    def push_statements(self, *stmts: ASTNode):
        self.statements.extend(stmts)

    def to_json(self) -> dict:
        return {"type": "Program", "body": [s.to_json() for s in self.statements]}


@dataclass
class Literal(ASTNode):
    type: LiteralType["Number", "String", "Boolean"]
    value: int | float | str | bool
    json: dict = field(default_factory=dict)

    def __post_init__(self):
        match self.type:
            case "Number":
                if isinstance(self.value, Token):
                    self.value = self.value.value
                elif not isinstance(self.value, (float, int)):
                    raise ParserError("Unsupported Literal[Number] value type.")
                self.json = {"type": "Literal[Number]", "value": self.value}

            case "String":
                if isinstance(self.value, Token):
                    self.value = self.value.value
                elif not isinstance(self.value, str):
                    raise ParserError("Unsupported Literal[String] value type.")
                self.json = {"type": "Literal[String]", "value": self.value}

            case "Boolean":
                if not isinstance(self.value, bool):
                    raise ParserError("Unsupported Literal[Boolean] value type.")
                self.json = {"type": "Literal[Boolean]", "value": self.value}

            case _:
                raise ParserError(f"Unknown Literal type: {self.type}.")

    def to_json(self):
        return self.json


@dataclass
class Identifier(ASTNode):
    value: str

    def __init__(self, token_or_str: Token | str):
        self.value = (
            token_or_str.value if isinstance(token_or_str, Token) else token_or_str
        )
        if not isinstance(self.value, str):
            raise ParserError("Identifier value must be a string")

    def to_json(self):
        return {"type": "Identifier", "value": self.value}


@dataclass
class AssignmentStatement(ASTNode):
    target: Identifier
    value: ASTNode

    def to_json(self):
        return {
            "type": "Assignment",
            "target": self.target.to_json(),
            "value": self.value.to_json(),
        }


@dataclass
class BinaryOperation(ASTNode):
    """+, -, *, /, %"""

    left: ASTNode
    op: Token
    right: ASTNode

    def to_json(self):
        return {
            "type": "Binary Expression",
            "operator": self.op.value,
            "left": self.left.to_json(),
            "right": self.right.to_json(),
        }


@dataclass
class UnaryOperation(ASTNode):
    """Unary operators: -, +, !"""

    op: Token
    operand: ASTNode

    def to_json(self):
        return {
            "type": "Unary Expression",
            "operator": self.op.value,
            "operand": self.operand.to_json(),
        }


@dataclass
class BooleanOperation(ASTNode):
    op1: ASTNode
    operation: str
    op2: ASTNode

    def __init__(self, op1: ASTNode, operation: Token, op2: ASTNode):
        self.op1 = op1
        self.operation = operation.value
        self.op2 = op2

    def to_json(self):
        return {
            "type": "Boolean Expression",
            "Expression": {
                "Operation": self.operation,
                "Operand1": self.op1.to_json(),
                "Operand2": self.op2.to_json(),
            },
        }


class IfStatement(ASTNode):
    def __init__(
        self,
        condition: BooleanOperation,
        body: BlockStatement,
        elif_list: list[tuple[ASTNode, BlockStatement]] | None = None,
        else_body: BlockStatement | None = None,
    ):
        self.condition = condition
        self.body = body
        self.elif_list = elif_list or []
        self.else_body = else_body

    def to_json(self):
        j = {
            "type": "If Statement",
            "If": {
                "condition": self.condition.to_json(),
                "body": self.body.to_json(),
            },
        }
        if self.elif_list:
            j["Elif"] = [
                {"condition": c.to_json(), "body": b.to_json()}
                for c, b in self.elif_list
            ]
        if self.else_body:
            j["Else"] = self.else_body.to_json()

        return j


@dataclass
class WhileStatement(ASTNode):
    condition: BooleanOperation
    body: BlockStatement

    def to_json(self):
        return {
            "type": "While Statement",
            "condition": self.condition.to_json(),
            "body": self.body.to_json(),
        }


@dataclass
class FunctionDeclarationStatement(ASTNode):
    name: Identifier
    body: BlockStatement

    def to_json(self):
        return {
            "type": "While Statement",
            "condition": self.condition.to_json(),
            "body": self.body.to_json(),
        }


@dataclass
class FunctionCallStatement(ASTNode):
    name: str
    args: list[ASTNode]
    kwargs: dict[str, ASTNode] = field(default_factory=dict)

    def to_json(self):
        return {
            "type": "Function Call",
            "name": self.name,
            "args": [a.to_json() for a in self.args],
            "kwargs": {k: v.to_json() for k, v in self.kwargs.items()},
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

    def parse_identifier(
        self,
    ) -> Identifier | AssignmentStatement | FunctionCallStatement:
        id_node = Identifier(self.cur_tok)
        self.advance()

        # Call
        if self.cur_tok.type == TokenType.LPAREN:
            return self.parse_call(id_node.value)
        # Assignment
        elif self.cur_tok.type == TokenType.ASSIGN:
            self.advance()
            value = self.parse_expression()
            expr = AssignmentStatement(id_node, value)
            return expr

        return id_node

    def parse_if(self) -> IfStatement:
        self.advance()  # skip 'if'

        self.expect(TokenType.LPAREN)  # the `(condition)` must be put in paren-s
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)

        body = self.parse_block_statement()

        elifs: list[tuple[ASTNode, BlockStatement]] = []
        else_body = None

        while self.cur_tok.type == TokenType.ELIF:
            self.advance()

            self.expect(TokenType.LPAREN)
            elif_cond: BooleanOperation = self.parse_expression()
            self.expect(TokenType.RPAREN)

            elif_body = self.parse_block_statement()

            elifs.append((elif_cond, elif_body))

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

    def parse_func(self, name):
        self.advance()  # skip func

    def parse_call(self, name) -> FunctionCallStatement:
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
        return FunctionCallStatement(name, args, kwargs)

    def parse_block_statement(self) -> BlockStatement:
        self.expect(TokenType.LBRACE)
        stmts = []
        while (
            self.cur_tok.type != TokenType.RBRACE and self.cur_tok.type != TokenType.EOF
        ):
            s = self.parse_statement()
            if s is not None:
                stmts.append(s)

        if self.cur_tok.type == TokenType.EOF:
            raise ParserError(
                f"Unexpected end of file: expected '}}' to close block at line {self.tokens[-1].pos[0]}"
            )

        self.expect(TokenType.RBRACE)
        return BlockStatement(stmts)

    def parse_expression(self) -> ASTNode:
        """Expressions are mathematical or boolean expressions like `a + b` or `a != b`."""
        result = self.parse_comparison_expr()
        if result is None:
            raise ParserError(f"Expected expression at {self.cur_tok.pos}")
        return result

    def parse_comparison_expr(self) -> ASTNode | None:
        left = self.parse_additive_expr()
        if left is None:
            raise ParserError(
                f"Expected expression in comparison at {self.cur_tok.pos}"
            )

        while self.cur_tok.type in COMPARISONS:
            op = self.cur_tok
            self.advance()
            right = self.parse_additive_expr()
            if right is None:
                raise ParserError(
                    f"Expected expression after '{op.value}' operator at {op.pos}"
                )
            left = BooleanOperation(left, op, right)
        return left

    def parse_additive_expr(self) -> ASTNode | None:
        left = self.parse_term_expr()
        while self.cur_tok.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.cur_tok
            self.advance()
            right = self.parse_term_expr()
            left = BinaryOperation(left, op, right)
        return left

    def parse_term_expr(self) -> ASTNode | None:
        left = self.parse_factor_expr()
        while self.cur_tok.type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.cur_tok
            self.advance()
            right = self.parse_factor_expr()
            left = BinaryOperation(left, op, right)
        return left

    def parse_factor_expr(self) -> ASTNode | None:
        left = self.parse_unary_expr()
        while self.cur_tok.type == TokenType.POWER:
            op = self.cur_tok
            self.advance()
            right = self.parse_unary_expr()
            left = BinaryOperation(left, op, right)
        return left

    def parse_unary_expr(self) -> ASTNode | None:
        """Parse unary operators: -, +, !"""
        tok = self.cur_tok

        if tok.type in (TokenType.MINUS, TokenType.PLUS):
            op = self.cur_tok
            self.advance()
            operand = self.parse_unary_expr()  # Right associative
            if operand is None:
                raise ParserError(
                    f"Expected expression after unary '{op.value}' at {op.pos}"
                )
            return UnaryOperation(op, operand)

        elif tok.type == TokenType.NOT:  # Assuming TokenType.NOT exists for '!'
            op = self.cur_tok
            self.advance()
            operand = self.parse_unary_expr()
            if operand is None:
                raise ParserError(f"Expected expression after NOT '!' at {op.pos}")
            return UnaryOperation(op, operand)

        return self.parse_primary_expr()

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

        else:
            raise ParserError(
                f"Unexpected token in expression: {tok.type} at {tok.pos}"
            )

    def serialize(self, path: str):
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.AST.to_json(), f, indent=4)
