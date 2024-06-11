# Assemble each instruction
two_input_simple_ops = {"add", "sub", "and", "or"}
comparison_ops = {"gt", "lt", "eq"}
one_input_ops = {"neg", "not"}
amount_of_return_calls_for_the_comparison_ops = 0
push_D_register_on_the_stack = "\n@SP\nM=M+1\nA=M-1\nM=D\n"
segment_map = {
    "argument": "ARG",
    "local": "LCL",
    "this": "THIS",
    "that": "THAT",
}

math_op_map = {
        "add": "D=D+M",
        "sub": "D=M-D",
        "and": "D=D&M",
        "or": "D=D|M",
    }
math_op_map_with_M = {
        "add": "M=D+M",
        "sub": "M=M-D",
        "and": "M=D&M",
        "or": "M=D|M",
    }

def is_reachable(segment, index):
    return (
        segment in {"pointer", "temp"}
        or segment == "constant"
        or segment == "static"
        or (segment in segment_map and int(index) < 4)
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
        elif index < 7:
            return f"@{base_segment}\nA=M+1\n" + "A=A+1\n" * (index - 1)
    return f"@{index}\nD=A\n@{segment_map[segment]}\nA=D+M\n"


def load_address(segment, index,name_of_file):
    index = int(index)
    if segment == "constant" and index not in {-1, 0, 1}:
        return f"@{index}\nD=A\n"
    if segment == "static":
        return f"@{name_of_file}.{index}\nD=A\n"
    if segment in {"pointer", "temp"}:
        base_address = 3 if segment == "pointer" else 5
        return f"@{base_address + index}\nD=A\n"
    if segment in segment_map:
        base_segment = segment_map[segment]
        if index == 0:
            return f"@{base_segment}\nD=M\n"
        elif index < 4:
            return f"@{base_segment}\nD=M+1\n" + "D=D+1\n" * (index - 1)
    return f"@{index}\nD=A\n@{segment_map[segment]}\nD=D+M\n"

def load_value_at_address(segment, index, name_of_file):
    index = int(index)
    if segment == "constant" and index not in {-1, 0, 1}:
        return f"@{index}\nD=A\n"
    if segment == "constant" and index in {-1, 0, 1}:
        return f"D={index}\n"
    if segment == "static":
        return f"@{name_of_file}.{index}\nD=M\n"
    if segment in {"pointer", "temp"}:
        base_address = 3 if segment == "pointer" else 5
        return f"@{base_address + index}\nD=M\n"
    if segment in segment_map:
        base_segment = segment_map[segment]
        if index == 0:
            return f"@{base_segment}\nA=M\nD=M\n"
        elif index < 4:
            return f"@{base_segment}\nA=M+1\n" + "A=A+1\n" * (index - 1) + "D=M\n"
    return f"@{index}\nD=A\n@{segment_map[segment]}\nA=D+M\nD=M\n"


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
        return f"\n@{index}\nD=A\n{go_to_top_of_stack}M=D\n"

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
        return f"\n{decrement_stack_pointer}@{base_address + int(index)}\nM=D\n"

    if segment == "static":
        return f"\n{decrement_stack_pointer}@{name_of_file}.{index}\nM=D\n"

    address_code = go_to_address(segment, index, name_of_file)
    if int(index) < 7:
        return f"\n{decrement_stack_pointer}{address_code}M=D\n"

    return (
        f"\n@{index}\nD=A\n@{segment_map[segment]}\nD=D+M\n@R13\nM=D\n"
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

    if segment_map.get(pop_segment) and int(pop_index) >= 7:
        return (
            optimized_code
            + f"@{pop_index}\nD=A\n@{segment_map[pop_segment]}\nD=D+M\n@13\nM=D\n"
            + load_value_at_address(push_segment, push_index, name_of_file)
            + "@13\nA=M\nM=D\n\n"
        )
    # Else, store the value at the push address in the D register, then store in the pop adress
    else:
        return (
            optimized_code + 
            load_value_at_address(push_segment, push_index, name_of_file)
            + go_to_address(pop_segment, pop_index, name_of_file)
            + "M=D\n\n"
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

def set_D_regster_to_correct_value_from_two_pushes_and_a_two_input_math(instructions, name_of_file):
    A_math_op_map = {
        "add": "D=D+A",
        "sub": "D=A-D",
        "and": "D=D&A",
        "or": "D=D|A",
    }
    other_math_op_map = {
        "add": "D=D+M",
        "sub": "D=D-M",
        "and": "D=D&M",
        "or": "D=D|M",
    }
    
    push1, push2, math_instruction = instructions
    _, segment1, index1 = push1.split()
    _, segment2, index2 = push2.split()
    the_string_to_return = f"//{push1} {push2} {math_instruction}\n"

    # Check if both are constants
    if segment1 == "constant" and segment2 == "constant":
        value = 0
        if math_instruction == "add":
            value = int(index1) + int(index2)
        elif math_instruction == "sub":
            value = int(index1) - int(index2)
        elif math_instruction == "and":
            value = int(index1) & int(index2)
        elif math_instruction == "or":
            value = int(index1) | int(index2)
        
        if value in {0, -1, 1}:
            return "D=" + str(value) + "\n"
        else:
            return f"@{value}\nD=A\n"

    # Case where one is a constant
    if segment1 == "constant" or segment2 == "constant":
        the_constant_value = index1 if segment1 == "constant" else index2
        the_segment_value = segment1 if segment1 != "constant" else segment2
        the_index_value = index1 if segment1 != "constant" else index2

        if int(the_constant_value) in {-1, 1} and math_instruction in {"add", "sub"}:
            the_D_modifier = "+" if (math_instruction == "add" and the_constant_value == "1") or (math_instruction == "sub" and the_constant_value == "-1") else "-"
            return go_to_address(the_segment_value, the_index_value, name_of_file) + f"D=M{the_D_modifier}1\n"
        else:
            the_string_to_return += (load_value_at_address(the_segment_value, the_index_value, name_of_file) + go_to_address("constant", the_constant_value, name_of_file))
            if math_instruction == "sub":
                if segment1 != "constant":
                    return the_string_to_return + "D=D-A\n"
                return the_string_to_return + "D=A-D\n"
            else:
                return the_string_to_return + A_math_op_map[math_instruction] + "\n"
    
    # Case where both segments and indices are the same
    if segment1 == segment2 and index1 == index2:
        return the_string_to_return + load_value_at_address(segment1, index1, name_of_file) + math_op_map[math_instruction] + "\n"
    
    # If both addresses are unreachable
    if not is_reachable(segment1, index1) and not is_reachable(segment2, index2):
        return (the_string_to_return 
                + f"@{index1}\nD=A\n@{segment_map[segment1]}\nD=D+M\n@13\nM=D\n" 
                + load_value_at_address(segment2, index2, name_of_file) 
                + "@13\nA=M\n" + math_op_map[math_instruction] + "\n")
    
    # If segment1 is unreachable
    if not is_reachable(segment1, index1):
        return (the_string_to_return 
                + load_value_at_address(segment1, index1, name_of_file) 
                + go_to_address(segment2, index2, name_of_file) 
                + other_math_op_map[math_instruction] + "\n")

    # If segment2 is unreachable
    return (the_string_to_return 
            + load_value_at_address(segment2, index2, name_of_file) 
            + go_to_address(segment1, index1, name_of_file) 
            + math_op_map[math_instruction] + "\n")


#push, push, MATH
def convert_double_push_math_group(instructions, name_of_file):
    return set_D_regster_to_correct_value_from_two_pushes_and_a_two_input_math(instructions, name_of_file) + push_D_register_on_the_stack

def do_two_input_math_instruction_with_something_in_the_D_register_on_the_stack(math_instruction):
    return "@SP\nAM=M-1" + math_op_map_with_M[math_instruction]


#push, math or push MATH
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


#This is the case where it is: push push MATH (with either MATH, pop, or math)
def MATH_two_pushes(instructions, name_of_file, extra=""):
    the_string_to_return = f"\n//caught {instructions} with {extra}\n"

    # Case: Just two pushes and a math
    if not extra:
        return convert_double_push_math_group(instructions, name_of_file)
    
    # Split extra for reuse
    extra_parts = extra.split()

    if extra_parts[0] == "pop":
        push1_addr = instructions[0].split()[1:3]
        push2_addr = instructions[1].split()[1:3]
        pop_addr = extra_parts[1:3]

        # Case where all the addresses are the same
        if push1_addr == push2_addr == pop_addr:
            return the_string_to_return + go_to_address(*push1_addr, name_of_file) + "D=M\n" + math_op_map_with_M[instructions[2]] + "\n"

        # Case where pop address matches one of the pushes
        for push_addr in [push1_addr, push2_addr]:
            if pop_addr == push_addr:
                other_push_addr = push2_addr if push_addr == push1_addr else push1_addr
                  # Special case: first push address equals pop address, second push is "constant 1", math instruction is "sub"
                if push_addr == push1_addr and other_push_addr == ["constant", "1"] and instructions[2] == "sub":
                    return the_string_to_return + go_to_address(*push_addr, name_of_file) + "M=M-1\n"
                if other_push_addr == ["constant", "1"] and instructions[2] == "add":
                    return the_string_to_return + go_to_address(*pop_addr, name_of_file) + "M=M+1\n"
                if is_reachable(*pop_addr):
                    return (the_string_to_return 
                            + load_value_at_address(*other_push_addr, name_of_file) 
                            + go_to_address(*pop_addr, name_of_file) 
                            + math_op_map_with_M[instructions[2]] + "\n")
                else:
                    return (the_string_to_return 
                            + load_address(*pop_addr, name_of_file) 
                            + "@14\nM=D\n" 
                            + load_value_at_address(*other_push_addr, name_of_file) 
                            + "@14\nA=M\n" 
                            + math_op_map_with_M[instructions[2]] + "\n")
        
        # Case where pop address is unreachable
        if not is_reachable(*pop_addr):
            return (the_string_to_return 
                    + load_address(*pop_addr, name_of_file) 
                    + "@14\nM=D\n" 
                    + set_D_regster_to_correct_value_from_two_pushes_and_a_two_input_math(instructions, name_of_file) 
                    + "@14\nA=M\nM=D\n")
        else:
            return (the_string_to_return 
                    + set_D_regster_to_correct_value_from_two_pushes_and_a_two_input_math(instructions, name_of_file) 
                    + go_to_address(*pop_addr, name_of_file) 
                    + "M=D\n")

    # Case: two pushes and a math with a one-input math instruction
    if extra in one_input_ops:
        the_string_to_return += set_D_regster_to_correct_value_from_two_pushes_and_a_two_input_math(instructions, name_of_file)
        the_string_to_return += "\nD=-D\n" if extra == "not" else "\nD=!D\n"
        return the_string_to_return + push_D_register_on_the_stack
    
    # Case: two pushes and a math with a two-input math instruction
    the_string_to_return += (set_D_regster_to_correct_value_from_two_pushes_and_a_two_input_math(instructions, name_of_file) + "\n@SP\nA=M-1\n" + math_op_map_with_M[extra] + "\n")
    
    return the_string_to_return

#This is the case where it is: push math/MATH (with either MATH, pop, or math)
def math_one_push(instructions, name_of_file, extra=""):
    the_string_to_return = ""
    push_value = load_value_at_address(instructions[0].split()[1], instructions[0].split()[2], name_of_file)
    
    # Case 1: one push with a two-input math instruction
    if instructions[1] in two_input_simple_ops:
        the_string_to_return += push_value + "@SP\nA=M-1\n" + math_op_map_with_M[instructions[1]] + "\n"
    else:
        the_string_to_return += push_value + ("D=-D\n" if instructions[1] == "not" else "D=!D\n")

    if extra:
        extra_parts = extra.split()
        if extra in one_input_ops:
            the_string_to_return += ("M=-M\n" if extra == "not" else "M=!M\n")
        elif extra in two_input_simple_ops:
            if instructions[1] in two_input_simple_ops:
                the_string_to_return += "@SP\nAM=M-1\nA=A-1\n" + math_op_map_with_M[extra] + "\n"
            else:
                the_string_to_return += "@SP\nA=M-1\nA=A-1\n" + math_op_map_with_M[extra] + "\n"
        else:
            push_addr = instructions[0].split()[1:3]
            pop_addr = extra_parts[1:3]
            
            # Case where pop address is the same as push address
            if push_addr == pop_addr:
                the_string_to_return += go_to_address(*pop_addr, name_of_file) + "M=D\n"
            else:
                if is_reachable(*pop_addr):
                    the_string_to_return += go_to_address(*pop_addr, name_of_file) + "M=D\n"
                else:
                    the_string_to_return = (load_address(*pop_addr, name_of_file) + "@13\nM=D\n"+ the_string_to_return + "@13\nA=M\nM=D\n")

    return f"\n//caught {instructions} with {extra}\n" + the_string_to_return
