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


def load_value_at_address(segment, index, name_of_file):
    if segment == "constant":
        return go_to_address(segment, index, name_of_file) + "D=A\n"
    return go_to_address(segment, index, name_of_file) + "D=M\n"


def sole_push_instruction(instruction, name_of_file):
    print(instruction)
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

    # If the pop address is unreachable, then store the address @13. Then store the push value in the D register and load at the address @13.

    if not (is_reachable(pop_segment, pop_index)):
        return (
            optimized_code
            + f"@{pop_index}\nD=A\n@{segment_map[pop_segment]}\nD=D+M\n@13\nM=D\n"
            + load_value_at_address(push_segment, push_index, name_of_file)
            + "@13\nA=M\nM=D\n"
        )
    # Else, store the value at the push address in the D register, then store in the pop adress
    else:
        return (
            load_value_at_address(push_segment, push_index, name_of_file)
            + go_to_address(pop_segment, pop_index, name_of_file)
            + "M=D\n"
        )


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
    # Possibilities: Two Constants, Reachable Adress and a constant, Unreachable Address and a constant, two reachable address, two 
    # unreachable addresses, one reachable and one not.
    
    #Two constants: Hard Code it
    #RA + Const : Store Const in the D reg
    #UnRa + Const : Store address of Unra @13, then store Const in D
    #Ra + Ra : Store the first in the D reg then go to the second
    #UnRa + Ra: Store address of Unra @13, then store Ra in D
    #UnRa + UnRa" Store address of the first UnRa @13. Then store UnRa in D.

    #Idea: If Unra, always store @13. If a RA or Const, store in the D register.
    push1, push2, math_instruction = instructions
    _, segment1, index1 = push1.split()
    _, segment2, index2 = push2.split()

    if segment1 == "constant" and segment2 == "constant":
        value = 0
        match math_instruction:
            case "add":
                value = int(index1) + int(index2)
            case "sub":
                value = int(index1) - int(index2)
            case "and":
                value = int(index1) & int(index2)
            case "or":
                value = int(index1) | int(index2)
        return sole_push_instruction("push constant " + str(value), name_of_file)

    the_string_to_return = ""

    math_op_map = {
        "add": "D=D+M",
        "sub": "D=M-D",
        "and": "D=D&M",
        "or": "D=D|M",
    }

    other_math_op_map = {
        "add": "D=D+M",
        "sub": "D=D-M",
        "and": "D=D&M",
        "or": "D=D|M",
    }

    A_math_op_map = {
        "add": "D=D+A",
        "sub": "D=A-D",
        "and": "D=D&A",
        "or": "D=D|A",
    }
    
    #Case where they're not both reachable
    if not(is_reachable(segment1, index1, name_of_file)) or not(is_reachable(segment2, index2, name_of_file)):
        if not(is_reachable(segment1, index1, name_of_file)) and not(is_reachable(segment2, index2, name_of_file)):
            the_string_to_return += f"@{index1}\nD=A\n@{segment_map[segment1]}\nD=D+M\n@13\nM=D\n" + go_to_address(segment2, index2, name_of_file) + "D=M\n@13\nA=M\n" + math_op_map[math_instruction] + "\n"
        elif is_reachable(segment1, index1, name_of_file) and not(is_reachable(segment2, index2, name_of_file)):
            the_string_to_return += f"@{index2}\nD=A\n@{segment_map[segment2]}\nD=D+M\n@13\nM=D\n" + load_value_at_address(segment1, index1, name_of_file) + "@13\nA=M\n" + other_math_op_map[math_instruction] + "\n"
        else:
            the_string_to_return += f"@{index1}\nD=A\n@{segment_map[segment1]}\nD=D+M\n@13\nM=D\n" + load_value_at_address(segment2, index2, name_of_file) + "@13\nA=M\n" + math_op_map[math_instruction] + "\n"
    else:
        #Case where they're both reachable
        the_string_to_return += load_value_at_address(segment1, index1, name_of_file) + go_to_address(segment2, index2, name_of_file)
    #By this point, I have to be careful whether the first or second value is @ the D reg. (since subtraction is not communative)

    return the_string_to_return


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
