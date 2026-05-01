import os, sys

import src.lexer as lexer
# import src.parser as parser
# import src.compiler as compiler

from src.errors import NovaScriptError

_script_arguments_flags = {
    "-d": "debug",
    "--debug": "debug",
    "-t": "target_script",
    "--target": "target_script",
    "-h": "help",
    "--help": "help",
}
_script_extensions = [".ns"]

def _validate_script(script_file_name: str) -> None:
    if not os.path.exists(script_file_name):
        raise Exception(f"File not found: {script_file_name}")

    if not any(script_file_name.endswith(ex) for ex in _script_extensions):
        raise Exception(
            f"Source script file must have one of {_script_extensions} extension."
        )

def _show_arguments_hint() -> None:
    print("\nNovaScript V2 Usage:")
    print("  python main.py <source_file.ns> [flags]")
    print("\nAvailable flags:")
    for flag, action in _script_arguments_flags.items():
        print(f"  {flag.ljust(10)} -> {action}")
    print()

def _process_args(args: list[str]) -> dict:
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
        
        if flag_name not in _script_arguments_flags:
            raise Exception(f"Unknown flag '{flag_name}'. Call '--help' for usage.")
        
        flag_type = _script_arguments_flags[flag_name]

        # Логіка для значень
        if len(parts) > 1:
            # Якщо є '=', записуємо значення (наприклад, для target_script)
            res[flag_type] = parts[1]
        else:
            # Якщо '=' немає, це булевий прапорець (True)
            res[flag_type] = True

    # Якщо попросили допомогу — виводимо і виходимо
    if res["help"]:
        _show_arguments_hint()
        sys.exit(0)

    # Валідація скрипта, якщо він вказаний
    if res["source_script"]:
        _validate_script(res["source_script"])
    
    return res

def _print_lexer_debug(TOKENS):
    print("Lexer execution. Generated tokens: \n")
    string = ""
    for i in TOKENS:
        string += str(i) + "\n"

    print(string)
def _print_parser_debug(AST):
    pass
def _print_compiler_debug(BYTECODE):
    pass

def compile_script(args: list[str]) -> None:
    script_config = _process_args(args)

    src: str | None = script_config["source_script"]
    debug: bool = script_config["debug"]
    target: str | None = script_config["target_script"]

    src_code: list[str] = []
    with open(src, "r") as file:
        src_code = file.readlines()

    TOKENS: list[lexer.Token] = lexer.Lexer(src_code).tokenize()
    # AST = parser.get_ast(TOKENS)
    # COMPILER = compiler.Compiler()
    # BYTECODE = COMPILER.make_file()
    if debug:
        _print_lexer_debug(TOKENS)
        # _print_parser_debug(AST)
        # _print_compiler_debug(BYTECODE)

    # return


if __name__ == "__main__":
    args = ["example1.ns", "-d"]
    # args = sys.argv[1:]
    compile_script(args)

    # print('Hello World!')
