"""
NovaScriptV2 - Compiler
Made by Minkx1.
"""

from bytecode import Instr, Bytecode, BinaryOp, Label
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
        raise Exception(f"Немає методу visit для {type(node).__name__}")
    
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
    def __init__(self, AST: 'AbstractSyntaxTree', environment: dict):
        super().__init__(AST, environment)
        self.bytecode = Bytecode()
        # Для Python 3.11+ LOAD_GLOBAL потребує флаг (True - globals, False - builtins)
        self.is_modern_python = True 

    def emit(self, name: str, *arg):
        self.bytecode.append(Instr(name, *arg))

    def visit_AbstractSyntaxTree(self, node: 'AbstractSyntaxTree'):
        for stmt in node.statements:
            self.visit(stmt)
        # В кінці програми Python завжди має бути RETURN_VALUE
        self.emit('LOAD_CONST', None)
        self.emit('RETURN_VALUE')

    def visit_LiteralNumber(self, node: 'LiteralNumber'):
        self.emit('LOAD_CONST', node.value)
    def visit_LiteralString(self, node: 'LiteralString'):
        self.emit('LOAD_CONST', node.value)
    def visit_Identifier(self, node: 'Identifier'):
        self.emit('LOAD_NAME', node.value)

    def visit_Assign(self, node: 'Assign'):
        self.visit(node.value)
        self.emit('STORE_NAME', node.target.value)

    def visit_BinOp(self, node: 'BinOp'):
        self.visit(node.left)
        self.visit(node.right)
        
        if self.is_modern_python:
            # op_map = {
            #     '+': 'BinaryOp.ADD',
            #     '-': 'BINARY_OP_SUBTRACT',
            #     '*': 'BINARY_OP_MULTIPLY',
            #     '/': 'BINARY_OP_TRUE_DIVIDE',
            #     '%': 'BINARY_OP_REMAINDER',
            #     '**':'BINARY_OP_POWER'
            # }
            op_map = {
                '+': BinaryOp.ADD,
                '-': BinaryOp.SUBTRACT,
                '*': BinaryOp.MULTIPLY,
                '/': BinaryOp.TRUE_DIVIDE,
                '%': BinaryOp.REMAINDER,
                '**': BinaryOp.POWER
            }  
            self.emit("BINARY_OP", op_map[node.op.value])
        else:
            op_map = {
                '+': 'BINARY_ADD',
                '-': 'BINARY_SUBTRACT',
                '*': 'BINARY_MULTIPLY',
                '/': 'BINARY_TRUE_DIVIDE',
                '%': 'BINARY_MODULO',
                '**': 'BINARY_POWER'
            }    
            # Примітка: В Python 3.11+ назви деяких інструкцій змінилися на BINARY_OP
            self.emit(op_map[node.op.value])
    
    def visit_Call(self, node: "Call"):
        if self.is_modern_python:
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
        else:
            raise NotImplementedError("Calling instructions for python3.10- are not implemented yet.")
        
    def execute(self, finish_and_wait:bool = True):
        if not self.bytecode:
            self.compile()

        start_time = perf_counter()
        exec(self.bytecode.to_code(), self.ENV)

        if finish_and_wait: 
            self.finish_and_wait(start_time)