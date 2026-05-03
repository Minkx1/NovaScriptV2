"""
NovaScriptV2 - Main EntryPoint
Made by Minkx1.
"""

import os, sys

from rich import print

import src.lexer as lexer
import src.parser as parser
import src.compiler as compiler

from src.errors import NovaScriptError

class NovaScript:
    _script_arguments_flags = {
        "-d": "debug",
        "--debug": "debug",
        "-t": "target_script",
        "--target": "target_script",
        "-h": "help",
        "--help": "help",
    }
    _script_extensions = [".ns"]

    def __init__(self, sys_args: list[str]):
        self.sys_args = sys_args

    @staticmethod
    def _validate_script(script_file_name: str) -> None:
        if not os.path.exists(script_file_name):
            raise Exception(f"File not found: {script_file_name}")

        if not any(script_file_name.endswith(ex) for ex in NovaScript._script_extensions):
            raise Exception(f"Source script file must have one of {NovaScript._script_extensions} extension.")

    @staticmethod
    def _show_arguments_hint() -> None:
        print("\nNovaScript V2 Usage:")
        print("  python main.py <source_file.ns> [flags]")
        print("\nAvailable flags:")
        for flag, action in NovaScript._script_arguments_flags.items():
            print(f"  {flag.ljust(10)} -> {action}")
        print()

    def _process_args(self) -> dict:
        args = self.sys_args
        res = {
            "source_script": None,
            "debug": False,
            "help": False,
            "target_script": None,
        }

        for arg in args:
            if not arg.startswith("-"):
                # Якщо це шлях до файлу
                res["source_script"] = arg
                continue
            
            # Обробка прапорців (можуть бути як --debug, так і --target=out.py)
            parts = arg.split("=", 1)
            flag_name = parts[0]
            
            if flag_name not in NovaScript._script_arguments_flags:
                raise Exception(f"Unknown flag '{flag_name}'. Call '--help' for usage.")
            
            flag_type =NovaScript. _script_arguments_flags[flag_name]

            # Логіка для значень
            if len(parts) > 1:
                # Якщо є '=', записуємо значення (наприклад, для target_script)
                res[flag_type] = parts[1]
            else:
                # Якщо '=' немає, це булевий прапорець (True)
                res[flag_type] = True

        # Якщо попросили допомогу — виводимо і виходимо
        if res["help"]:
            NovaScript._show_arguments_hint()
            sys.exit(0)

        # Валідація скрипта, якщо він вказаний
        if res["source_script"]:
            NovaScript._validate_script(res["source_script"])
        
        return res

    @staticmethod
    def _print_lexer_debug(TOKENS:list[lexer.Token]): # , 
        print("================")
        print(f"Lexer execution. Generated {len(TOKENS)} tokens: \n")
        print([tok for tok in TOKENS])
        print("================\n")
    @staticmethod
    def _print_parser_debug(AST:parser.AbstractSyntaxTree):
        print("================")
        print(f"Abstract Syntax Tree: \n")
        print(AST.to_json())
        print("================\n")
    @staticmethod
    def _print_compiler_debug(BYTECODE):
        print("================")
        print(f"Bytecode: \n")
        for instr in BYTECODE:
            print(instr)
        print("================\n")
    
    def _print_debug(self):
        self._print_lexer_debug(self.TOKENS)
        self._print_parser_debug(self.AST)
        self._print_compiler_debug(self.COMPILER.bytecode)

    def execute(self) -> None:
        script_config = self._process_args()

        src: str | None = script_config["source_script"]
        debug: bool = script_config["debug"]
        # target: str | None = script_config["target_script"]

        src_code: list[str] = []
        with open(src, "r") as file:
            src_code = file.readlines()

        self.TOKENS = lexer.Lexer(src_code).tokenize()
        self.AST = parser.Parser(self.TOKENS).parse_program()
        self.COMPILER = compiler.PyCompiler(self.AST)

        self.COMPILER.compile()

        if debug:
            self._print_debug()

        self.COMPILER.execute()

if __name__ == "__main__":
    args = ["example1.ns", "-d"]
    # args = sys.argv[1:]
    NS = NovaScript(args)
    NS.execute()