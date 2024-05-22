local lfs = require "lfs"
local bit = bit32 or require("bit")

RAM_MAP = {
    constant = 0,
    argument = 2,
    pointer = 3,
    this = 3,
    that = 4,
    temp = 5
}

function FileExists(name)
    local f=io.open(name,"r")
    if f~=nil then io.close(f) return true else return false end
 end

function ConvertPushInstruction(PushInstruction)
    local words = {}
    for word in PushInstruction:gmatch("%S+") do
        table.insert(words, word)
    end
    
    local segment = words[2]
    local index = tonumber(words[3])
    local address = (segment == "local") and 1 or RAM_MAP[segment]
    local TheStringToReturn
    print("Push Instruction is " .. PushInstruction)
    print("\t" .. words[2])
    print("\t" .. address .. "\n")

    if segment == "constant" then
        TheStringToReturn = "@" .. index .. "\nD=A\n"
    else
        TheStringToReturn = "@" .. address .. "\nA=M"
        for i = 1, index do
            TheStringToReturn = TheStringToReturn .. "\nA=A+1"
        end
        TheStringToReturn = TheStringToReturn .. "\nD=M\n"
    end
    
    return TheStringToReturn .. "@SP\nA=M\nM=D\n@SP\nM=M+1\n"
end

function ConvertPopInstruction(PopInstruction)
    local words = {}
    for word in PopInstruction:gmatch("%S+") do
        table.insert(words, word)
    end
    local segment = words[2]
    local index = tonumber(words[3])
    local address = (segment == "local") and 1 or RAM_MAP[segment]
    print("Pop Instruction is " .. PopInstruction)
    print("\t" .. words[2])
    print("\t" .. address .. "\n")
    local TheStringToReturn = "@SP\nA=M\nA=A-1\nD=M\nM=0\n@SP\nM=M-1\n@" .. address .. "\nA=M"
    for i = 1, index do
        TheStringToReturn = TheStringToReturn .. "\nA=A+1"
    end
    TheStringToReturn = TheStringToReturn .. "\nM=D\n"
    
    return TheStringToReturn
end

function DoMath(MathInstruction)
    --The VM represents true and false as -1 (minus one, 0xFFFF) and 0 (zero, 0x0000), respectively.
    TheStringToReturn = ""
    --There are two types of MathInstructions, those with one input and those with two
    TwoInputInstructions = {"sub", "add", "eg", "gt", "lt", "and", "or"}
    OneInputInstructions = {"neg", "not"}
        --Go to the stack pointer and store the first value in the D register. Then go to the next value
        TheStringToReturn = "@SP\nA=M\nA=A-1\nA=A-1\nD=M\nA=A+1\n"
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
            -- ^@: Matches lines that start with '@' (A-instruction)
            output_file:write(ConvertPushInstruction(line))
        elseif line:match("^pop") then
            -- ^%(: Excludes lines that start with '(' (labels)
            output_file:write(ConvertPopInstruction(line))
            else 
                if line:match("^add") or line:match("^sub") then
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