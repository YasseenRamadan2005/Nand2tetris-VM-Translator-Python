# Assemble each instruction
two_input_simple_ops = {"add", "sub", "and", "or"}
comparison_ops = {"gt", "lt", "eq"}
one_input_ops = {"neg", "not"}
amount_of_return_calls_for_the_comparison_ops = 0

segment_map = {
    "argument": "ARG",
    "local": "LCL",
    "this": "THIS",
    "that": "THAT",
}


def is_reachable(segment, index):
    return (
        segment in {"pointer", "temp"}
        or segment == "constant"
        or segment == "static"
        or (segment in segment_map and int(index) < 8)
    )


def go_to_address(segment, index, name_of_file):
    index = int(index)
    if segment == "constant" and index not in {-1, 0, 1}:
        return f"@{index}\n"
    if segment == "static":
        return f"@{name_of_file}.{index}\n"
    if segment in {"pointer", "temp"}:
        base_address = 3 if segment == "pointer" else 5
        return f"@{base_address + index}\n"
    if segment in segment_map:
        base_segment = segment_map[segment]
        if index == 0:
            return f"@{base_segment}\nA=M\n"
        elif index < 8:
            return f"@{base_segment}\nA=M+1\n" + "A=A+1\n" * (index - 1)
    return f"@{index}\nD=A\n@{segment_map[segment]}\nA=D+M\n"


def sole_push_instruction(instruction, name_of_file):
    _, segment, index = instruction.split()
    go_to_top_of_stack = "@SP\nM=M+1\nA=M-1\n"

    # Load constant value onto stack
    if segment == "constant":
        if index == "0":
            return go_to_top_of_stack + "M=0\n"
        elif index == "1":
            return go_to_top_of_stack + "M=1\n"
        return f"@{index}\nD=A\n{go_to_top_of_stack}M=D\n"

    # Load value from segment onto stack
    address_code = go_to_address(segment, index, name_of_file)
    return (
        "//"
        + instruction
        + "\n"
        + address_code
        + "D=M\n"
        + go_to_top_of_stack
        + "M=D\n"
    )


def sole_pop_instruction(instruction, name_of_file):
    _, segment, index = instruction.split()
    decrement_stack_pointer = "@SP\nAM=M-1\nD=M\n"

    # Store value from stack into segment
    if segment in {"pointer", "temp"}:
        base_address = 3 if segment == "pointer" else 5
        return f"{decrement_stack_pointer}@{base_address + int(index)}\nM=D\n"

    if segment == "static":
        return f"{decrement_stack_pointer}@{name_of_file}.{index}\nM=D\n"

    address_code = go_to_address(segment, index, name_of_file)
    if int(index) < 8:
        return f"{decrement_stack_pointer}{address_code}M=D\n"

    return (
        f"@{index}\nD=A\n@{segment_map[segment]}\nD=D+M\n@R13\nM=D\n"
        f"{decrement_stack_pointer}"
        f"@R13\nA=M\nM=D\n"
    )


def push_pop_parser(instructions, name_of_file):
    the_amount_of_lines = len(instructions)
    the_string_to_return = ""
    for i in range(the_amount_of_lines // 2):
        the_string_to_return += push_pop_optimized(
            instructions[i], instructions[the_amount_of_lines - 1 - i], name_of_file
        )
    return the_string_to_return


def push_pop_optimized(push_instruction, pop_instruction, name_of_file):
    _, push_segment, push_index = push_instruction.split()
    _, pop_segment, pop_index = pop_instruction.split()
    optimized_code = "//" + push_instruction + " , " + pop_instruction + "\n"

    # Load value from push segment
    if push_segment == "constant":
        optimized_code += f"@{push_index}\nD=A\n"
    else:
        optimized_code += (
            go_to_address(push_segment, push_index, name_of_file) + "D=M\n"
        )

    # Store value into pop segment
    if pop_segment in {"pointer", "temp"}:
        base_address = 3 if pop_segment == "pointer" else 5
        optimized_code += f"@{base_address + int(pop_index)}\nM=D\n"
    elif pop_segment == "static":
        optimized_code += f"@{name_of_file}.{pop_index}\nM=D\n"
    else:
        if int(pop_index) < 8:
            optimized_code += (
                go_to_address(pop_segment, pop_index, name_of_file) + "M=D\n"
            )
        else:
            optimized_code += (
                f"@R13\nM=D\n"
                f"@{pop_index}\nD=A\n@{segment_map[pop_segment]}\nD=D+M\n@R14\nM=D\n"
                f"@R13\nD=M\n@R14\nA=M\nM=D\n"
            )

    return optimized_code


def convert_sole_math_instr(math_instruction):
    global amount_of_return_calls_for_the_comparison_ops
    the_string_to_return = ""

    if math_instruction in two_input_simple_ops:
        the_string_to_return = "@SP\nAM=M-1\nD=M\nA=A-1\n"
        op_map = {"add": "M=D+M\n", "sub": "M=M-D\n", "and": "M=D&M\n", "or": "M=D|M\n"}
        the_string_to_return += op_map[math_instruction]
        return the_string_to_return

    if math_instruction in comparison_ops:
        comp_map = {"lt": "M=-1\n", "eq": "M=0\n", "gt": "M=1\n"}
        return_label = (
            f"RETURN.FROM.COMP.OPS.{amount_of_return_calls_for_the_comparison_ops}"
        )
        the_string_to_return = (
            f"@{return_label}\nD=A\n@14\n"
            f"{comp_map[math_instruction]}"
            "@COMP_BEGIN\n0;JMP\n"
            f"({return_label})\n"
        )
        amount_of_return_calls_for_the_comparison_ops += 1
        return the_string_to_return

    the_string_to_return = "@SP\nA=M-1\n"
    if math_instruction == "neg":
        the_string_to_return += "M=-M\n"
    elif math_instruction == "not":
        the_string_to_return += "M=!M\n"

    return the_string_to_return


def convert_double_push_math_group(instructions, name_of_file):
    push1, push2, math_instruction = instructions
    _, segment1, index1 = push1.split()
    _, segment2, index2 = push2.split()

    math_op_map = {
        "add": "D=D+M",
        "sub": "D=M-D",
        "and": "D=D&M",
        "or": "D=D|M",
    }

    A_math_op_map = {
        "add": "D=D+A",
        "sub": "D=A-D",
        "and": "D=D&A",
        "or": "D=D|A",
    }

    address1 = go_to_address(segment1, index1, name_of_file)
    address2 = go_to_address(segment2, index2, name_of_file)

    def load_value(segment, address):
        if segment == "constant":
            return address + "D=A\n"  # Load constant value into D
        else:
            return address + "D=M\n"  # Load value from memory into D

    comment = f'// "{push1}, {push2}, {math_instruction}"\n'
    result_push = "@SP\nAM=M+1\nA=A-1\nM=D  // Push the result to the stack\n"

    # Handle the case where the same address is used twice
    if segment1 == segment2 and index1 == index2:
        return (
            comment
            + address1
            + "D=M\n"  # Load value from memory into D
            + math_op_map[math_instruction]
            + "\n"
            + result_push
        )

    # Handle both reachable segments
    if is_reachable(segment1, index1) and is_reachable(segment2, index2):
        return (
            comment
            + load_value(segment2, address2)
            + address1
            + (
                A_math_op_map[math_instruction]
                if segment1 == "constant"
                else math_op_map[math_instruction]
            )
            + "\n"
            + result_push
        )

    # Handle only one reachable segment
    if is_reachable(segment1, index1) or is_reachable(segment2, index2):
        (
            reachable_segment,
            unreachable_segment,
            reachable_address,
            unreachable_address,
        ) = (
            (segment1, segment2, address1, address2)
            if is_reachable(segment1, index1)
            else (segment2, segment1, address2, address1)
        )
        return (
            comment
            + unreachable_address
            + "D=M\n"
            + load_value(reachable_segment, reachable_address)
            + (
                A_math_op_map[math_instruction]
                if unreachable_segment == "constant"
                else math_op_map[math_instruction]
            )
            + "\n"
            + result_push
        )

    # Both addresses are unreachable
    return (
        comment
        + load_value(segment1, address1)
        + "@13\nM=D  // Store the first value in R13\n"
        + address2
        + "D=M\n@13\n"
        + math_op_map[math_instruction]
        + "\n"
        + result_push
    )


def convert_push_math_group(instructions, name_of_file):
    push_instruction, math_instruction = instructions
    _, segment, index = push_instruction.split()

    # Define the mapping for simple arithmetic/logical operations
    math_op_map = {
        "add": "D+M",
        "sub": "M-D",
        "and": "D&M",
        "or": "D|M",
    }

    # Define the mapping for unary operations
    unary_op_map = {
        "neg": "-M",
        "not": "!M",
    }

    address = go_to_address(segment, index, name_of_file)

    def load_value(segment, address):
        if segment == "constant":
            return address + "D=A\n"  # Load constant value into D
        else:
            return address + "D=M\n"  # Load value from memory into D

    comment = f'// "{push_instruction}, {math_instruction}"\n'
    result_push = "@SP\nA=M-1\n"

    # Handle the push followed by a two-input math operation
    if math_instruction in math_op_map:
        return (
            comment
            + load_value(segment, address)
            + result_push
            + "M="
            + math_op_map[math_instruction]
            + "\n"
        )

    # Handle the push followed by a unary math operation
    if math_instruction in unary_op_map:
        return (
            comment
            + load_value(segment, address)
            + unary_op_map[math_instruction]
            + "\n"
            + result_push
            + "M=D\n"
        )

    # If the math instruction is not recognized
    return f"// Unsupported instruction: {math_instruction}\n"
