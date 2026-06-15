import opcode


class Instr:
    def __init__(self, opcode: str, arg=None):
        self.opcode = opcode
        self.arg = arg

    def __repr__(self) -> str:
        return f"{self.opcode:<20} {self.arg}"


class Label:
    _id_counter = 0

    def __init__(self):
        self.id = Label._id_counter
        Label._id_counter += 1
        self.offset: int | None = None

    def __repr__(self) -> str:
        return f"<Label {self.id}>"

    def __str__(self):
        return f"<Label {self.id}>"


class BinaryOp:
    ADD = 0
    MULTIPLY = 5
    REMAINDER = 6
    POWER = 8
    SUBTRACT = 10
    TRUE_DIVIDE = 11


class Compare:
    LT = 2
    LE = 26
    EQ = 40
    NE = 55
    GT = 68
    GE = 92


class Bytecode:
    def __init__(self):
        self.instructions: list[Instr | Label] = []

    def append(self, item: Instr | Label) -> None:
        self.instructions.append(item)

    def __iter__(self):
        return iter(self.instructions)

    def __len__(self) -> int:
        return len(self.instructions)

    def __getitem__(self, index):
        return self.instructions[index]

    def _normalize_name_arg(self, arg):
        if isinstance(arg, tuple) and len(arg) >= 2 and isinstance(arg[1], str):
            return arg[1]
        return arg

    def _get_name_index(self, name, names, names_map):
        if name in names_map:
            return names_map[name]
        index = len(names)
        names_map[name] = index
        names.append(name)
        return index

    def _get_const_index(self, const, consts, consts_map):
        if const in consts_map:
            return consts_map[const]
        index = len(consts)
        consts_map[const] = index
        consts.append(const)
        return index

    def _encode_instruction(self, op, arg):
        if arg is None:
            arg = 0
        if arg < 0:
            raise ValueError(f"Negative argument is not supported: {arg}")
        parts = bytearray()
        ext_args: list[int] = []
        while arg > 0xFF:
            ext_args.append((arg >> 8) & 0xFF)
            arg >>= 8
        for ext_arg in reversed(ext_args):
            parts.append(opcode.opmap["EXTENDED_ARG"])
            parts.append(ext_arg)
        parts.append(opcode.opmap[op])
        parts.append(arg & 0xFF)
        return bytes(parts)

    def _instruction_size(self, op, arg) -> int:
        if arg is None:
            arg = 0
        size = 2
        while arg > 0xFF:
            size += 2
            arg >>= 8
        return size

    def _get_inline_cache_entries(self, op: str) -> int:
        if op == "CACHE":
            return 0
        op_num = opcode.opmap.get(op)
        if op_num is None:
            return 0
        inline_cache_entries = getattr(opcode, "_inline_cache_entries", None)
        if inline_cache_entries is None:
            return 0
        return inline_cache_entries[op_num]

    def _resolve_arg(self, instr, offset, consts, consts_map, names, names_map, label_positions):
        op = instr.opcode
        arg = instr.arg
        if op == "CACHE":
            return 0
        if op in {"LOAD_CONST", "KW_NAMES"}:
            return self._get_const_index(arg, consts, consts_map)
        if op in {"LOAD_NAME", "STORE_NAME"}:
            return self._get_name_index(arg, names, names_map)
        if op == "LOAD_GLOBAL":
            arg = self._normalize_name_arg(arg)
            return self._get_name_index(arg, names, names_map)
        if op in {"POP_JUMP_IF_FALSE", "JUMP_FORWARD", "JUMP_BACKWARD"}:
            if not isinstance(arg, Label):
                raise ValueError(f"Jump instruction requires a Label argument, got {arg!r}")
            if arg.offset is None:
                raise ValueError("Label offset is not assigned")
            target = arg.offset
            if opcode.opmap[op] in opcode.hasjrel:
                return abs(target - (offset + self._instruction_size(op, 0))) // 2
            return target // 2
        if op in {"COMPARE_OP", "BINARY_OP", "CALL"}:
            return arg if arg is not None else 0
        if op == "RETURN_VALUE":
            return 0
        if op == "UNARY_NEGATIVE" or op == "UNARY_NOT":
            return 0
        if op == "POP_TOP":
            return 0
        if op == "RESUME":
            return 0
        if op == "RETURN_CONST":
            return self._get_const_index(arg, consts, consts_map)
        raise ValueError(f"Unsupported opcode in assembler: {op}")

    def _build_tables(self):
        consts = [None]
        consts_map = {None: 0}
        names: list[str] = []
        names_map: dict[str, int] = {}

        for instr in self.instructions:
            if isinstance(instr, Label):
                continue
            op = instr.opcode
            if op in {"LOAD_CONST", "KW_NAMES", "RETURN_CONST"}:
                self._get_const_index(instr.arg, consts, consts_map)
            elif op in {"LOAD_NAME", "STORE_NAME"}:
                self._get_name_index(instr.arg, names, names_map)
            elif op == "LOAD_GLOBAL":
                normalized = self._normalize_name_arg(instr.arg)
                self._get_name_index(normalized, names, names_map)
        return consts, consts_map, names, names_map

    def _insert_cache_instructions(self, instructions: list[Instr | Label]) -> list[Instr | Label]:
        result: list[Instr | Label] = []
        for instr in instructions:
            result.append(instr)
            if isinstance(instr, Instr) and instr.opcode != "CACHE":
                count = self._get_inline_cache_entries(instr.opcode)
                for _ in range(count):
                    result.append(Instr("CACHE", 0))
        return result

    def to_code(self):
        if not self.instructions:
            template = compile("pass", "<generated>", "exec")
            return template

        instructions = list(self.instructions)
        first_instr = next((instr for instr in instructions if not isinstance(instr, Label)), None)
        if not (isinstance(first_instr, Instr) and first_instr.opcode == "RESUME"):
            instructions.insert(0, Instr("RESUME", 0))

        instructions = self._insert_cache_instructions(instructions)
        consts, consts_map, names, names_map = self._build_tables()
        label_positions: dict[Label, int] = {}
        offsets: list[int] = [0] * len(instructions)

        # Iteratively resolve labels and instruction sizes.
        changed = True
        while changed:
            changed = False
            offset = 0
            for index, instr in enumerate(instructions):
                offsets[index] = offset
                if isinstance(instr, Label):
                    if instr.offset != offset:
                        instr.offset = offset
                        changed = True
                    label_positions[instr] = offset
                    continue
                size = self._instruction_size(instr.opcode, 0)
                if instr.opcode in {"POP_JUMP_IF_FALSE", "JUMP_FORWARD", "JUMP_BACKWARD"}:
                    if not isinstance(instr.arg, Label):
                        raise ValueError("Jump argument must be a Label")
                    target = instr.arg.offset if instr.arg.offset is not None else offset
                    op_num = opcode.opmap.get(instr.opcode)
                    if op_num in opcode.hasjrel:
                        arg = abs(target - (offset + size)) // 2
                    else:
                        arg = target // 2
                    new_size = self._instruction_size(instr.opcode, arg)
                    if new_size != size:
                        size = new_size
                        changed = True
                offset += size

        code_bytes = bytearray()
        for index, instr in enumerate(instructions):
            if isinstance(instr, Label):
                continue
            op = instr.opcode
            op_num = opcode.opmap.get(op)
            if op_num is None:
                raise ValueError(f"Unknown opcode: {op}")
            arg = self._resolve_arg(instr, offsets[index], consts, consts_map, names, names_map, label_positions)
            code_bytes.extend(self._encode_instruction(op, arg))

        max_stack = 0
        current_stack = 0
        i = 0
        while i < len(code_bytes):
            op = code_bytes[i]
            arg = code_bytes[i + 1]
            try:
                effect = opcode.stack_effect(op, arg)
            except ValueError:
                effect = 0
            current_stack += effect
            if current_stack > max_stack:
                max_stack = current_stack
            i += 2

        template = compile("pass", "<generated>", "exec")
        return template.replace(
            co_code=bytes(code_bytes),
            co_consts=tuple(consts),
            co_names=tuple(names),
            co_stacksize=max_stack,
            co_firstlineno=1,
            co_linetable=template.co_linetable,
            co_exceptiontable=template.co_exceptiontable,
        )
