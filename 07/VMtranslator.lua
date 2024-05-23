local lfs = require "lfs"

Segments = {
    ["argument"] = "ARG",
    ["local"] = "LCL",
    ["this"] = "THIS",
    ["that"] = "THAT"
}

function ConvertSegementIndexIntoAddress()

end

function FileExists(name)
    local f = io.open(name, "r")
    if f ~= nil then
        io.close(f)
        return true
    else return false end
end

function ConvertPushInstruction(instruction)
    --[[
        "push segment index"
        Sitaution to store the data in the D register:
            "push constant k"
                    @k
                    D=A
            "push argument/local/this/that k"
                K is 0:
                    @ARG/LCL/THIS/THAT
                    A=M
                K is 1:
                    @ARG/LCL/THIS/THAT
                    A=M+1
                K is 2:
                    @ARG/LCL/THIS/THAT
                    A=M+1
                    A=A+1
                Else:
                    @ARG/LCL/THIS/THAT
                    D=M
                    @k
                    A=D+A
                    D=M
                Always with D=M
            "push pointer/temp k"
                @(3/5 + k)
                A=M
                D=M
    Always end with D=M except for pushing a constant
    ]]
    local command, segment, index = instruction:match("(%S+)%s+(%S+)%s+(%d+)")
    local asm = "\n//Start push instruction (" .. instruction .. ")\n"

    if command == "push" then
        if segment == "constant" then
            asm = asm .. "@" .. index .. "\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        elseif Segments[segment] then
            local base = Segments[segment]
            local offset = tonumber(index)
            asm = asm .. "@" .. base .. "\n"
            if offset == 0 then
                asm = asm .. "A=M\nD=M\n"
            elseif offset == 1 then
                asm = asm .. "A=M+1\nD=M\n"
            elseif offset == 2 then
                asm = asm .. "A=M+1\nA=A+1\nD=M\n"
            else
                asm = asm .. "D=M\n@" .. index .. "\nA=D+A\nD=M\n"
            end
            asm = asm .. "@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        elseif segment == "pointer" then
            asm = asm .. "@" .. (3 + tonumber(index)) .. "\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        elseif segment == "temp" then
            asm = asm .. "@" .. (5 + tonumber(index)) .. "\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        end
    end
    return asm
end

function ConvertPopInstruction(PopInstruction)
    --[[
    "pop segment index"
        Sitaution:
            pop argument/local/this/that k for k < 8
                @SP
                M=M-1
                A=M
                D=M
                M=0
                @ARG/LCL/THIS/THAT
                {
                    A=M if 0

                    A=M+1 if 1

                    A=M+1
                    A=A+1 if 2

                    A=M+1
                    A=M+1
                    A=A+1 if 3

                    ...
                }
                M=D
            pop argument/local/this/that k for k>=8
                @k
                D=A
                @ARG/LCL/THIS/THAT
                D=D+M
                @13
                M=D
                @SP
                M=M-1
                A=M
                D=M
                M=0
                @13
                A=M
                M=D
            "pop pointer/temp k"
                @SP
                M=M-1
                A=M
                D=M
                M=0
                @(3/5 + k) //calculate this
                A=M
                M=D
    Always end with M=D
    ]]

    local command, segment, index = PopInstruction:match("(%S+)%s+(%S+)%s+(%d+)")
    local asm = "\n//Start pop instruction (" .. PopInstruction .. ")\n"

    if command == "pop" then
        local popfromstack = "@SP\nM=M-1\nA=M\nD=M\nM=0\n//Go to the address\n@"
        if Segments[segment] then
            local base = Segments[segment]
            local offset = tonumber(index)
            if offset < 8 then
                asm = asm .. popfromstack .. base .. "\n"
                if offset == 0 then
                    asm = asm .. "A=M\n"
                elseif offset == 1 then
                    asm = asm .. "A=M+1\n"
                elseif offset == 2 then
                    asm = asm .. "A=M+1\nA=A+1\n"
                else
                    asm = asm .. "A=M+1\n"
                    for i = 2, offset do
                        asm = asm .. "A=A+1\n"
                    end
                end
            else
                --By this point, store the address in the general purpose register for later
                asm = asm .. "@" .. base .."\nD=M\n@" .. index .. "\nD=D+A\n@13\nM=D\n" .. popfromstack .. "13\nA=M\n"
            end
            asm = asm .. "M=D\n"
        elseif segment == "pointer" then
            asm = asm .. popfromstack .. (3 + tonumber(index)) .. "\nM=D\n"
        elseif segment == "temp" then
            asm = asm.. popfromstack .. (5 + tonumber(index)) .. "\nM=D\n"
        end
    end
    return asm
end

function DoMath(MathInstruction)
    --The VM represents true and false as -1 (minus one, 0xFFFF) and 0 (zero, 0x0000), respectively.
    TheStringToReturn = "\n//Math: " .. MathInstruction .. "\n"
    --There are two types of MathInstructions, those with one input and those with two
    TwoInputInstructions = { "sub", "add", "eg", "gt", "lt", "and", "or" }
    OneInputInstructions = { "neg", "not" }
    --Go to the stack pointer and store the first value in the D register. Then go to the next value
    TheStringToReturn = TheStringToReturn .. "@SP\nA=M-1\nA=A-1\nD=M\nA=A+1\n"
    if MathInstruction == "sub" then
        TheStringToReturn = TheStringToReturn .. "D=D-M\n"
    end
    if MathInstruction == "add" then
        TheStringToReturn = TheStringToReturn .. "D=D+M\n"
    end
    TheStringToReturn = TheStringToReturn .. "M=0\nA=A-1\nM=D\n@SP\nM=M-1\n"
    return TheStringToReturn
end

function CreateTheAsmFile(filename)
    local file = io.open(filename .. ".vm", 'rb')
    local parsed = file:read('*a'):gsub("\r\n", "\n")
    file:close()
    parsed = parsed:gsub("//.-\n", "")
    local output_file = io.open(filename .. ".asm", 'w')
    for line in parsed:gmatch("[^\n]+") do
        if line:match("^push") then
            print(line)
            -- ^@: Matches lines that start with '@' (A-instruction)
            output_file:write(ConvertPushInstruction(line))
        elseif line:match("^pop") then
            print(line)
            -- ^%(: Excludes lines that start with '(' (labels)
            output_file:write(ConvertPopInstruction(line))
        else
            if line:match("^add") or line:match("^sub") then
                print(line)
                output_file:write(DoMath(line))
            end
        end
    end
    output_file:close()
end

-- First check if the input is a .vm or a path
if string.sub(arg[1], -3) == ".vm" then
    if FileExists(arg[1]) then
        print("The file exists")
    else
        print("The file doesn't exist")
    end
else
    if not lfs.chdir(arg[1]) then
        print("Directory doesn't exist")
    else
        --Now check if the file exists there

        if FileExists(arg[1]:gsub("^.*/", "") .. ".vm") then
            --print(lfs.currentdir())
            --print(arg[1]:match("([^/]+)$") .. ".vm")
            CreateTheAsmFile(arg[1]:match("([^/]+)$"))
        else
            print("The file doesn't exist")
        end
    end
end
