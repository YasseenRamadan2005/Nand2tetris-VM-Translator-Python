import os
import sys
from assembler import (
    sole_push_instruction,
    sole_pop_instruction,
    convert_sole_math_instr,
    push_pop_parser,
    math_one_push,
    MATH_two_pushes,
    convert_call,
    convert_function,
    convert_if_goto,
    convert_goto,
    convert_label,
    convert_return
)


#This is the amount of time a function calls another function, not the amount a time a function is called.
amount_of_function_calls = {"Sys.init":0}
has_done_the_boot_strap = False

# Define sets of different types of operations
simple_two_input_ops = {"add", "sub", "and", "or"}
comp_ops = {"gt", "lt", "eq"}
one_input_ops = {"neg", "not"}
has_seen_comp_ops = False
current_function = ""
def count_consecutive_ops(lines, start_index, op):
    """Counts consecutive occurrences of a given operation starting from a specific index."""
    count = 0
    while (
        start_index + count < len(lines) and lines[start_index + count].split()[0] == op
    ):
        count += 1
    return count


def remove_comments(lines):
    """Removes comments from each line in the given list of lines."""
    cleaned_lines = []
    for line in lines:
        # Remove everything after "//" and strip any leading/trailing whitespace
        cleaned_line = line.split("//")[0].strip()
        if cleaned_line:  # Only add non-empty lines
            cleaned_lines.append(cleaned_line)
    return cleaned_lines


def grouper_and_translate(instructions, name_of_file):
    """Groups and translates VM instructions to assembly code."""
    asm_code = ""
    global has_seen_comp_ops
    global current_function
    if (("\neq" in instructions) or ("\nlt" in instructions) or ("\ngt" in instructions)) and not(has_seen_comp_ops):
        # Add assembly code for comparison operations
        has_seen_comp_ops = True
        asm_code += "@SKIP\n0;JMP\n(COMP_BEGIN)\n@13\nM=D //Store the return address @13\n@SP\nA=M-1\nD=M\nA=A-1\nD=M-D //Calculate the difference\n\n@15\nM=D\n@14 //Check the flag @14\nD=M\n@EQ_BEGIN\nD;JEQ\n@LT_BEGIN\nD;JLT\n\n//By this case, this is the greater than subroutine\n@15\nD=M\n@RETURN_TRUE\nD;JGT\n@RETURN_FALSE\n0;JMP\n\n(EQ_BEGIN)\n@15\nD=M\n@RETURN_TRUE\nD;JEQ\n@RETURN_FALSE\n0;JMP\n\n(LT_BEGIN)\n@15\nD=M\n@RETURN_TRUE\nD;JLT\n@RETURN_FALSE\n0;JMP\n\n(RETURN_TRUE)\nD=-1;\n@COMPLETE\n0;JMP\n\n(RETURN_FALSE)\nD=0;\n@COMPLETE\n0;JMP\n\n(COMPLETE)\n@SP\nAM=M-1\nA=A-1\nM=D\n@13\nA=M\n0;JMP\n(SKIP)\n\n"

    lines = instructions.splitlines()
    lines = remove_comments(lines)  # Remove comments from lines
    index = 0
    while index < len(lines):
        current_line = lines[index]
        parts = current_line.split()
        operation = parts[0]
        if operation == "push":
            push_count = count_consecutive_ops(lines, index, "push")
            if index + push_count < len(lines):
                next_op = lines[index + push_count].split()[0]
            else:
                next_op = None
            if next_op == "pop":
                # If consecutive push and pop operations, parse them together
                pop_count = count_consecutive_ops(lines, index + push_count, "pop")
                if push_count == pop_count:
                    asm_code += push_pop_parser(lines[index : index + push_count + pop_count], name_of_file)
                else:
                    if push_count > pop_count:
                        # If not equal number of push and pop operations, parse individually
                        for i in range(push_count - pop_count):
                            asm_code += sole_push_instruction(lines[index + i], name_of_file)
                        asm_code += push_pop_parser(lines[index + push_count - pop_count : index + push_count + pop_count], name_of_file,)
                    else:
                        # Case where more pops than pushes
                        asm_code += push_pop_parser(lines[index : index + push_count + push_count], name_of_file)
                        for i in range(pop_count - push_count):
                            asm_code += sole_pop_instruction(lines[index + i + push_count + push_count],name_of_file)
                index += push_count + pop_count
            elif next_op in simple_two_input_ops or next_op in one_input_ops:
                # First, check if the previous the last 2 are a push
                distance_traveled = 0
                if push_count == 1:
                    # Only one push and a math instruction.
                    # Now check if there are further instructions
                    if index + push_count == len(lines) - 1 or not (
                        lines[index + push_count + 1] in simple_two_input_ops
                        or lines[index + push_count + 1] in one_input_ops
                        or lines[index + push_count + 1].split()[0] == "pop"
                    ):
                        asm_code += math_one_push(lines[index : index + push_count + 1], name_of_file)
                        distance_traveled = 1
                    else:
                        asm_code += math_one_push(lines[index : index + push_count + 1], name_of_file, lines[index + push_count + 1])
                        distance_traveled = 2
                elif next_op in one_input_ops:
                    # By this case I know there exists at least on extra push despite having a one input math instruction
                    for i in range(push_count - 1):
                        asm_code += sole_push_instruction(
                            lines[index + i], name_of_file
                        )
                    if index + push_count == len(lines) - 1 or not (
                        lines[index + push_count + 1] in simple_two_input_ops
                        or lines[index + push_count + 1] in one_input_ops
                        or lines[index + push_count + 1].split()[0] == "pop"
                    ):
                        asm_code += math_one_push(lines[index + push_count - 1 : index + push_count + 1], name_of_file)
                        distance_traveled = 1
                    else:
                        next_next_next_op = lines[index + push_count + 1]
                        asm_code += math_one_push(lines[index + push_count - 1 : index + push_count + 1], name_of_file, lines[index + push_count + 1])
                        distance_traveled = 2
                    math_one_push(
                        lines[index + push_count - 1 : index + push_count + 1],
                        name_of_file,
                    )
                else:
                    if push_count > 2:
                        for i in range(push_count - 2):
                            asm_code += sole_push_instruction(
                                lines[index + i], name_of_file
                            )
                    # By this case I know there exists a push, push, math instruction
                    if index + push_count == len(lines) - 1 or not (
                        lines[index + push_count + 1] in simple_two_input_ops
                        or lines[index + push_count + 1] in one_input_ops
                        or lines[index + push_count + 1].split()[0] == "pop"
                    ):
                        asm_code += MATH_two_pushes(
                            lines[index + push_count - 2 : index + push_count + 1],
                            name_of_file,
                        )
                        distance_traveled = 1
                    else:
                        asm_code += MATH_two_pushes(
                            lines[index + push_count - 2 : index + push_count + 1],
                            name_of_file,
                            lines[index + push_count + 1],
                        )
                        distance_traveled = 2
                    # Now clean up any extra pushes
                index += push_count + distance_traveled
            else:
                # Parse push instructions individually
                for i in range(push_count):
                    asm_code += sole_push_instruction(lines[index + i], name_of_file)
                index += push_count
        else:
            if operation in {"pop"}:
                # Parse pop instruction
                asm_code += sole_pop_instruction(current_line, name_of_file)
            elif (operation in simple_two_input_ops or operation in one_input_ops or operation in comp_ops):
                # Parse math instructions
                asm_code += convert_sole_math_instr(operation)
            elif operation == "label":
                asm_code += convert_label(current_line, current_function)
            elif operation == "return":
                asm_code += "//Returning:\n\n" + convert_return()
            elif operation == "call":
                name_of_function = current_line.split()[1]
                amount_of_function_calls[current_function] += 1
                asm_code += convert_call(current_line, current_function, amount_of_function_calls[current_function])
            elif operation == "if-goto":
                asm_code += convert_if_goto(current_line,current_function)
            elif operation == "function":
                name_of_function = current_line.split()[1]
                current_function = name_of_function
                amount_of_function_calls[current_function] = 1
                asm_code += convert_function(current_line, name_of_file)
            elif operation == "goto":
                asm_code += convert_goto(current_line,current_function)
            index += 1
    return asm_code



def translate_file(file_path):
    with open(file_path, 'r') as file:
        instructions = file.read()
    return grouper_and_translate(instructions, os.path.basename(file_path))

def process_vm_files(directory_path):
    lowest_directory_name = get_lowest_directory_name(directory_path)
    output_file_path = os.path.join(directory_path, f"{lowest_directory_name}.asm")
    
    vm_files = [f for f in os.listdir(directory_path) if f.endswith('.vm')]
    if not vm_files:
        print("No .vm files found in the directory.")
        return
    
    has_sys_vm = 'Sys.vm' in vm_files
    
    with open(output_file_path, 'w') as output_file:
        if has_sys_vm:
            # Write the initialization code
            output_file.write("@256\nD=A\n@SP\nM=D\n" + convert_call("call Sys.init 0", "init", 1))
        
        # Process each .vm file and append the result to the output file
        for vm_file in vm_files:
            vm_file_path = os.path.join(directory_path, vm_file)
            with open(vm_file_path, 'r') as file:
                instructions = file.read()
            assembly_code = grouper_and_translate(instructions, vm_file)
            output_file.write(assembly_code)
    
    print(f"Assembly code written to {output_file_path}")

def get_lowest_directory_name(directory_path):
    return os.path.basename(directory_path.rstrip(os.sep))

def main():
    """Main function to handle file or directory input and translate .vm files to .asm."""
    if len(sys.argv) != 2:
        print("Usage: python translator.py <inputfile.vm | inputdirectory>")
        sys.exit(1)

    input_path = sys.argv[1]
    if os.path.isdir(input_path):
        # If input is a directory, translate all .vm files in the directory
        process_vm_files(input_path)
    elif os.path.isfile(input_path) and input_path.endswith(".vm"):
        # If input is a single .vm file, translate it
        asm_file_path = os.path.splitext(input_path)[0] + ".asm"
        with open(asm_file_path, "w") as asm_file:
            asm_file.write(translate_file(input_path))
        print("Translation complete: " + asm_file_path)
    else:
        # Invalid input path
        print("Error: Invalid input path. Provide a .vm file or a directory containing .vm files.")
        sys.exit(1)

if __name__ == "__main__":
    main()

