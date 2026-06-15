"""
NovaScriptV2 - Intermidiate-Code Generator
Made by Minkx1.
"""

from bytecode import Instr, Bytecode, BinaryOp, Compare, Label
from time import perf_counter

from .parser import ASTNode, AbstractSyntaxTree, Literal, Identifier, AssignmentStatement, BinaryOperation, UnaryOperation, BooleanOperation, BlockStatement, IfStatement, WhileStatement, FunctionCallStatement, FunctionDeclarationStatement 
from .errors import GeneratorError

class Instruction:
    def __init__(self, opcode: str, arg=None):
        self.opcode = opcode
        self.arg = arg

    def __repr__(self):
        return f"{self.opcode:<20} {self.arg}"

class BaseGenerator:
    def __init__(self, AST: AbstractSyntaxTree):
        self.AST = AST
        self.bytecode = None
        
        self.start_t = perf_counter()
        self.time = 0

    def generate(self):
        """Main function of `Generator` class. It starts from the top of AST and generates **intermediate bytecode**."""
        self.time = 0
        self.visit(self.AST)
        self.time = perf_counter() - self.start_t
    
        return self.bytecode

    def visit(self, node: ASTNode):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        raise GeneratorError(f"No method visit_{type(node).__name__}")
    
    def execute(self):
        raise NotImplementedError

    def finish_and_wait(self, execution_start_time:float=0):
        import time
        delta_t = time.perf_counter()-execution_start_time
        print(f"\n\nExecuted in {delta_t:0.4f} seconds.")
        try:
            input("Press <ENTER> to continue...")
        except KeyboardInterrupt:
            pass

# --- ПАЙТОН КОМПІЛЯТОР ---

class PyVMGenerator(BaseGenerator):
    __required_py_version__ = "3.11"

    def __init__(self, AST: AbstractSyntaxTree):
        super().__init__(AST)
        self.bytecode = Bytecode()
        self.ENV = {
            # built-in functions
            "print": print,
            "input": input,
            "to_int": int.__call__,
            "to_float": float.__call__,
            "to_str": str.__call__,
            "len": len
        }

        # Checking version of python
        import sys
        maj, min = sys.version_info.major, sys.version_info.minor
        if maj<3 or min<11:
            raise GeneratorError(f"Python Version {sys.version_info.major}.{sys.version_info.minor} is not compatible with this version of Pyhon Bytecode Compiler. Please ensure to have python {PyVMGenerator.__minimum_py_version__}")

    def emit(self, name: str, *arg):
        self.bytecode.append(Instr(name, *arg))

    def visit_AbstractSyntaxTree(self, node: AbstractSyntaxTree):
        for stmt in node.statements:
            self.visit(stmt)

        self.emit('LOAD_CONST', None)
        self.emit('RETURN_VALUE')
    
    def visit_BlockStatement(self, node: BlockStatement):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Literal(self, node: Literal):
        self.emit('LOAD_CONST', node.value)
    
    def visit_Identifier(self, node: Identifier):
        self.emit('LOAD_NAME', node.value)

    def visit_BooleanOperation(self, node: BooleanOperation):
        op1: ASTNode = node.op1
        op2: ASTNode = node.op2
        oper: str = node.operation
        self.visit(op1)
        self.visit(op2)

        compare_map = {
            '==': Compare.EQ,
            '!=': Compare.NE,
            '<': Compare.LT,
            '<=': Compare.LE,
            '>': Compare.GT,
            '>=': Compare.GE,
            # 'in': Compare.IN, тощо
        }
        self.emit('COMPARE_OP', compare_map[oper])


    def visit_IfStatement(self, node: IfStatement):
        end_label = Label()
    
        # IF
        else_label = Label()
        self.visit(node.condition)
        self.emit('POP_JUMP_IF_FALSE', else_label)
        
        self.visit(node.body)
        self.emit('JUMP_FORWARD', end_label)
        self.bytecode.append(else_label)

        # ELIFS
        if node.elif_list:
            for elif_cond, elif_body in node.elif_list:
                next_elif_label = Label()
                self.visit(elif_cond)
                self.emit('POP_JUMP_IF_FALSE', next_elif_label)
                
                self.visit(elif_body)
                self.emit('JUMP_FORWARD', end_label)
                self.bytecode.append(next_elif_label)

        # ELSE
        if node.else_body:
            self.visit(node.else_body)

        self.bytecode.append(end_label)

    def visit_WhileStatement(self, node: WhileStatement):
        start_label = Label()
        end_label = Label()

        self.bytecode.append(start_label)
        
        self.visit(node.condition)
        self.emit('POP_JUMP_IF_FALSE', end_label)

        self.visit(node.body)

        self.emit('JUMP_BACKWARD', start_label)
        
        self.bytecode.append(end_label)

    def visit_AssignmentStatement(self, node: AssignmentStatement):
        self.visit(node.value)
        self.emit('STORE_NAME', node.target.value)

    def visit_BinaryOperation(self, node: BinaryOperation):
        self.visit(node.left)
        self.visit(node.right)
        
        op_map = {
            '+': BinaryOp.ADD,
            '-': BinaryOp.SUBTRACT,
            '*': BinaryOp.MULTIPLY,
            '/': BinaryOp.TRUE_DIVIDE,
            '%': BinaryOp.REMAINDER,
            '**': BinaryOp.POWER
        }  
        self.emit("BINARY_OP", op_map[node.op.value])

    def visit_UnaryOperation(self, node: UnaryOperation):
        self.visit(node.operand)
        
        if node.op.value == '-':
            self.emit('UNARY_NEGATIVE')
        elif node.op.value == '+':
            pass  # +x is just x
        elif node.op.value == '!':
            self.emit('UNARY_NOT')
        else:
            raise GeneratorError(f"Unsupported unary operator: {node.op.value}")
    
    def visit_FunctionCallStatement(self, node: FunctionCallStatement):
        func_name = node.name
        args: list[ASTNode] = node.args
        kwargs: dict[str, ASTNode] = node.kwargs

        self.emit('LOAD_GLOBAL', (True, func_name))
        
        i = 0
        kw_list = []

        for arg in args:
            self.visit(arg) # Adds Args to stack
            i += 1

        for k, v in kwargs.items():
            kw_list.append(k)
            self.visit(v) # Adds keywords arguments value to stack
            i += 1
        kw_list = tuple(kw_list)

        self.emit('KW_NAMES', kw_list)
        self.emit('CALL', i)


class PyVMInterpreter(PyVMGenerator):

    def execute(self, finish_and_wait:bool = True):
        if not self.bytecode:
            self.generate()

        start_time = perf_counter()
        exec(self.bytecode.to_code(), self.ENV)

        if finish_and_wait: 
            self.finish_and_wait(start_time)