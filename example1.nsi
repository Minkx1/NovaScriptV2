@type com

<LOAD_GLOBAL arg=(True, 'println') location=None>
<LOAD_CONST arg='=== Розрахунок доходу ===' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_GLOBAL arg=(True, 'println') location=None>
<LOAD_CONST arg='Введи погодинну ставку:' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_GLOBAL arg=(True, 'to_float') location=None>
<LOAD_GLOBAL arg=(True, 'getln') location=None>
<LOAD_CONST arg='> ' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<STORE_NAME arg='rate' location=None>
<LOAD_GLOBAL arg=(True, 'println') location=None>
<LOAD_CONST arg='Введи кількість годин:' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_GLOBAL arg=(True, 'to_int') location=None>
<LOAD_GLOBAL arg=(True, 'getln') location=None>
<LOAD_CONST arg='> ' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<STORE_NAME arg='hours' location=None>
<LOAD_NAME arg='rate' location=None>
<LOAD_NAME arg='hours' location=None>
<BINARY_OP arg=<BinaryOp.MULTIPLY: 5> location=None>
<STORE_NAME arg='income' location=None>
<LOAD_GLOBAL arg=(True, 'println') location=None>
<LOAD_CONST arg='-----' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_GLOBAL arg=(True, 'println') location=None>
<LOAD_CONST arg='Ставка: ' location=None>
<LOAD_GLOBAL arg=(True, 'to_str') location=None>
<LOAD_NAME arg='rate' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<BINARY_OP arg=<BinaryOp.ADD: 0> location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_GLOBAL arg=(True, 'println') location=None>
<LOAD_CONST arg='Години: ' location=None>
<LOAD_GLOBAL arg=(True, 'to_str') location=None>
<LOAD_NAME arg='hours' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<BINARY_OP arg=<BinaryOp.ADD: 0> location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_GLOBAL arg=(True, 'println') location=None>
<LOAD_CONST arg='Дохід: ' location=None>
<LOAD_GLOBAL arg=(True, 'to_str') location=None>
<LOAD_NAME arg='income' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<BINARY_OP arg=<BinaryOp.ADD: 0> location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_GLOBAL arg=(True, 'println') location=None>
<LOAD_CONST arg='-----' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_GLOBAL arg=(True, 'println') location=None>
<LOAD_CONST arg='Подвійний дохід: ' location=None>
<LOAD_GLOBAL arg=(True, 'to_str') location=None>
<LOAD_GLOBAL arg=(True, 'to_float') location=None>
<LOAD_NAME arg='income' location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_CONST arg=2 location=None>
<BINARY_OP arg=<BinaryOp.MULTIPLY: 5> location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<BINARY_OP arg=<BinaryOp.ADD: 0> location=None>
<KW_NAMES arg=() location=None>
<CALL arg=1 location=None>
<LOAD_CONST arg=None location=None>
<RETURN_VALUE location=None>
