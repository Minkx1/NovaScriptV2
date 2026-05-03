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
    def __init__(self, AST: 'AbstractSyntaxTree'):
        self.AST = AST
        self.bytecode = None

    def compile(self):
        self.visit(self.AST)
        return self.bytecode

    def visit(self, node: 'ASTNode'):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: 'ASTNode'):
        raise Exception(f"Немає методу visit для {type(node).__name__}")
    
    def execute(self):
        raise NotImplementedError

# --- ПАЙТОН КОМПІЛЯТОР ---

class PyCompiler(BaseCompiler):
    def __init__(self, AST: 'AbstractSyntaxTree'):
        super().__init__(AST)
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

    def visit_Number(self, node: 'Number'):
        self.emit('LOAD_CONST', node.value)

    def visit_String(self, node: 'String'):
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

    def visit_STDOUTCall(self, node: 'STDOUTCall'):
        if self.is_modern_python:
            self.emit('LOAD_GLOBAL', (True, 'print'))
            self.visit(node.value)
            self.emit('LOAD_CONST', '')      # значення для end
            self.emit('LOAD_CONST', True)    # значення для flush
            
            self.emit('KW_NAMES', ('end', 'flush'))

            self.emit('CALL', 3)
            
        else:
            self.emit('LOAD_GLOBAL', (True, 'print'))
            
            self.visit(node.value)
            self.emit('LOAD_CONST', '')              # end=''
            self.emit('LOAD_CONST', True)            # flush=True
            self.emit('LOAD_CONST', ('end', 'flush'))
            
            self.emit('CALL_FUNCTION_KW', 3)

    def execute(self):
        if not self.bytecode:
            self.compile()
        exec(self.bytecode.to_code())