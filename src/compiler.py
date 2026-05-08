"""
NovaScriptV2 - Compiler
Made by Minkx1.
"""

from bytecode import Instr, Bytecode, BinaryOp, Compare, Label
from types import CodeType

from .parser import *
from .errors import CompilerError

class Instruction:
    def __init__(self, opcode: str, arg=None):
        self.opcode = opcode
        self.arg = arg

    def __repr__(self):
        return f"{self.opcode:<20} {self.arg}"

class BaseCompiler:
    def __init__(self, AST: 'AbstractSyntaxTree', environment: dict):
        self.AST = AST
        self.bytecode = None
        self.ENV = environment
        
        self.start_t = perf_counter()
        self.time = 0

    def compile(self):
        self.visit(self.AST)
        self.time = perf_counter() - self.start_t
        return self.bytecode

    def visit(self, node: 'ASTNode'):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: 'ASTNode'):
        raise CompilerError(f"No method visit_{type(node).__name__}")
    
    def execute(self):
        raise NotImplementedError

    def finish_and_wait(self, execution_start_time:float=0):
        import time
        delta_t = time.perf_counter()-execution_start_time
        print(f"\n\nExecuted in {delta_t:0.4f} seconds.")
        try:
            input("Press ENTER to continue...")
        except KeyboardInterrupt:
            pass

# --- ПАЙТОН КОМПІЛЯТОР ---

class PyCompiler(BaseCompiler):
    __minimum_py_version__ = "3.11"
    def __init__(self, AST: 'AbstractSyntaxTree', environment: dict):
        super().__init__(AST, environment)
        self.bytecode = Bytecode()

        import sys
        maj, min = sys.version_info.major, sys.version_info.minor
        if maj<3 or min<11:
            raise CompilerError(f"Python Version {sys.version_info.major}.{sys.version_info.minor} is not compatible with this version of Pyhon Bytecode Compiler. Please ensure to have python {PyCompiler.__minimum_py_version__}+")

    def emit(self, name: str, *arg):
        self.bytecode.append(Instr(name, *arg))

    def visit_AbstractSyntaxTree(self, node: 'AbstractSyntaxTree'):
        for stmt in node.statements:
            self.visit(stmt)

        self.emit('LOAD_CONST', None)
        self.emit('RETURN_VALUE')
    
    def visit_BlockStatement(self, node: "BlockStatement"):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Literal(self, node: 'Literal'):
        self.emit('LOAD_CONST', node.value)
    def visit_Identifier(self, node: 'Identifier'):
        self.emit('LOAD_NAME', node.value)

    def visit_BoolOp(self, node:"BoolOp"):
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


    def visit_IfStatement(self, node:"IfStatement"):
        end_label = Label()
    
        # IF
        else_label = Label()
        self.visit(node.condition)
        self.emit('POP_JUMP_IF_FALSE', else_label)
        
        self.visit(node.body)
        self.emit('JUMP_FORWARD', end_label)
        self.bytecode.append(else_label)

        # ELIFS
        if node.elif_dict:
            for elif_cond, elif_body in node.elif_dict.items():
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

    def visit_WhileStatement(self, node:"WhileStatement"):
        start_label = Label()
        end_label = Label()

        self.bytecode.append(start_label)
        
        self.visit(node.condition)
        self.emit('POP_JUMP_IF_FALSE', end_label)

        self.visit(node.body)

        self.emit('JUMP_BACKWARD', start_label)
        
        self.bytecode.append(end_label)

    def visit_Assign(self, node: 'Assign'):
        self.visit(node.value)
        self.emit('STORE_NAME', node.target.value)

    def visit_BinOp(self, node: 'BinOp'):
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
    
    def visit_Call(self, node: "Call"):
        func_name = node.name
        args:list[ASTNode] = node.args
        kwargs:dict[str, ASTNode] = node.kwargs

        self.emit('LOAD_GLOBAL', (True, func_name))
        
        i = 0
        kw_list = []

        for arg in args:
            self.visit(arg) # Adds Args to stack
            i += 1

        for k, v in kwargs:
            kw_list.append(k)
            self.visit(v) # Adds keywords arguments value to stack
            i += 1
        kw_list = tuple(kw_list)

        self.emit('KW_NAMES', kw_list)
        self.emit('CALL', i)
        
    def execute(self, finish_and_wait:bool = True):
        if not self.bytecode:
            self.compile()

        start_time = perf_counter()
        exec(self.bytecode.to_code(), self.ENV)

        if finish_and_wait: 
            self.finish_and_wait(start_time)