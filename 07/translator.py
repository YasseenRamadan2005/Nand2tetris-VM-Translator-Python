import os
import sys
from assembler import (
    sole_push_instruction,
    sole_pop_instruction,
    convert_sole_math_instr,
    convert_double_push_math_group,
    convert_push_math_group,
    push_pop_parser,
    push_pop_optimized,
)

# Define sets of different types of operations
simple_two_input_ops = {"add", "sub", "and", "or"}
comp_ops = {"gt", "lt", "eq"}
one_input_ops = {"neg", "not"}


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
    if "eq" in instructions or "lt" in instructions or "gt" in instructions:
        # Add assembly code for comparison operations
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
                # print(pop_count, push_count)
                if push_count == pop_count:
                    asm_code += push_pop_parser(
                        lines[index : index + push_count + pop_count], name_of_file
                    )
                else:
                    if push_count > pop_count:
                        # If not equal number of push and pop operations, parse individually
                        for i in range(push_count - pop_count):
                            asm_code += (
                                sole_push_instruction(lines[index + i], name_of_file)
                                + "\n"
                            )
                        asm_code += (
                            push_pop_parser(
                                lines[
                                    index
                                    + push_count
                                    - pop_count : index
                                    + push_count
                                    + pop_count
                                ],
                                name_of_file,
                            )
                            + "\n"
                        )
                    else:
                        print(lines[index : index + push_count + push_count])
                        asm_code += (
                            push_pop_parser(
                                lines[index : index + push_count + push_count],
                                name_of_file,
                            )
                            + "\n"
                        )
                        for i in range(pop_count - push_count):
                            print(lines[index + i + push_count + push_count])
                            asm_code += (
                                sole_pop_instruction(
                                    lines[index + i + push_count + push_count],
                                    name_of_file,
                                )
                                + "\n"
                            )
                index += push_count + pop_count
            elif next_op in simple_two_input_ops:
                if push_count == 2:  # Check if it's a double push math group
                    asm_code += (
                        convert_double_push_math_group(
                            lines[index : index + push_count + 1], name_of_file
                        )
                        + "\n"
                    )
                elif push_count == 1:  # It's a single push math group
                    asm_code += (
                        convert_push_math_group(
                            lines[index : index + push_count + 1], name_of_file
                        )
                        + "\n"
                    )
                else:
                    # Otherwise, parse individually
                    for i in range(push_count - 2):
                        asm_code += sole_push_instruction(
                            lines[index + i], name_of_file
                        )
                    asm_code += convert_double_push_math_group(
                        lines[index + push_count - 2 : index + push_count + 1],
                        name_of_file,
                    )
                index += push_count + 1
            else:
                # Parse push instructions individually
                for i in range(push_count):
                    asm_code += (
                        sole_push_instruction(lines[index + i], name_of_file) + "\n"
                    )
                index += push_count
        else:
            if operation in {"pop"}:
                # Parse pop instruction
                asm_code += sole_pop_instruction(current_line, name_of_file) + "\n"
            elif (
                operation in simple_two_input_ops
                or operation in one_input_ops
                or operation in comp_ops
            ):
                # Parse math instructions
                asm_code += convert_sole_math_instr(operation) + "\n"
            index += 1
    return asm_code


def translate_file(vm_file_path):
    """Translates a single .vm file to .asm."""
    name_of_file = os.path.splitext(os.path.basename(vm_file_path))[0]
    asm_file_path = os.path.splitext(vm_file_path)[0] + ".asm"
    with open(vm_file_path, "r") as vm_file:
        vm_instructions = vm_file.read()
    asm_code = grouper_and_translate(vm_instructions, name_of_file)
    with open(asm_file_path, "w") as asm_file:
        asm_file.write(asm_code)


def main():
    """Main function to handle file or directory input and translate .vm files to .asm."""
    if len(sys.argv) != 2:
        print("Usage: python translator.py <inputfile.vm | inputdirectory>")
        sys.exit(1)

    input_path = sys.argv[1]
    if os.path.isdir(input_path):
        # If input is a directory, translate all .vm files in the directory
        for file_name in os.listdir(input_path):
            if file_name.endswith(".vm"):
                translate_file(os.path.join(input_path, file_name))
    elif os.path.isfile(input_path) and input_path.endswith(".vm"):
        # If input is a single .vm file, translate it
        translate_file(input_path)
    else:
        # Invalid input path
        print(
            "Error: Invalid input path. Provide a .vm file or a directory containing .vm files."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
