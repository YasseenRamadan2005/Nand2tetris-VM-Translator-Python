local lfs = require "lfs"
local bit = bit32 or require("bit")

RAM_MAP = {
    constant = 0,
    arguement = 2,
    pointer = 3,
    this = 3,
    that = 4,
    temp = 5
}

function FileExists(name)
    local f=io.open(name,"r")
    if f~=nil then io.close(f) return true else return false end
 end

-- When pushing:
-- Go to the address, store the value in the data register, then go to the stack, and M=D. Then increment SP
-- When poppping:

function ConvertPushInstruction(PushInstruction)
    --In the form push segment index
    local words = {}
    for word in PushInstruction:gmatch("%S+") do
        table.insert(words,word)
    end
    TheValueFromTheRamMap = 0
    if words[2] == "local" then
        TheValueFromTheRamMap = 1 --local is a keyword, so use stupid trick
    else
        TheValueFromTheRamMap = RAM_MAP[words[2]]
    end
    if words[2] == "constant" then
        TheStringToReturn = "@" .. tostring(TheValueFromTheRamMap) .. "\nD=A\n"
    else
        TheStringToReturn = "@" .. tostring(TheValueFromTheRamMap) .. "\nA=M"
        --Then increment to the index
        for i = 1, tonumber(words[3]), 1 do
            TheStringToReturn = TheStringToReturn .. "\nA=A+1"
        end
        TheStringToReturn = TheStringToReturn .. "\nD=M\n"
    end
    return TheStringToReturn .. "@SP\nA=M\nM=D\n@SP\nM=M+1\n"
end
-- Go to the top of the stack. store the value in the D register. Then set value to 0. Decrement stack pointer. Then go to the address and set the value there to D.

function ConvertPopInstruction(PullInstruction)
    --In the form push segment index
    local words = {}
    for word in PullInstruction:gmatch("%S+") do
        table.insert(words,word)
    end
    TheValueFromTheRamMap = 0
    if words[2] == "local" then
        TheValueFromTheRamMap = 1 --local is a keyword, so use stupid trick
    else
        TheValueFromTheRamMap = RAM_MAP[words[2]]
    end
    TheStringToReturn = "@SP\nA=M\nD=M\nM=0\n@SP\nM=M-1\n@" .. tostring(TheValueFromTheRamMap) .. "\nA=M\n"
    --Then increment to the index
    for i = 1, tonumber(words[3]), 1 do
        TheStringToReturn = TheStringToReturn .. "A=A+1\n"
    end
    return TheStringToReturn .. "M=D"
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
            print("The file exists")
        else
            print("The file doesn't exist")
        end
    end
end
