// Initialize LCL[0] = 10
@10
D=A
@LCL
A=M
M=D

// Initialize ARG[2] = 22
@22
D=A
@ARG
A=M+1
A=A+1
M=D

// Initialize ARG[1] = 21
@21
D=A
@ARG
A=M+1
M=D

// Initialize THIS[6] = 36
@36
D=A
@THIS
A=M+1
A=A+1
A=A+1
A=A+1
A=A+1
A=A+1
M=D

// Initialize THAT[5] = 45
@45
D=A
@THAT
A=M+1
A=A+1
A=A+1
A=A+1
A=A+1
M=D

// Initialize THAT[2] = 42
@42
D=A
@THAT
A=M+1
A=A+1
M=D

// Initialize temp[6] = 510
@510
D=A
@11
M=D

// Push local 0 (10) onto the stack
// Push that 5 (42) onto the stack
// Add top two stack values (local 0 + that 5) (+1 NET STACK)
@THAT
D=M
@5
A=D+A
D=M
@LCL
A=M
D=D+M
@ARG
A=M+1
D=D-M
@SP
M=M+1
A=M-1
M=D


// Push this 6 (36) onto the stack twice,  add then subtract (NET ZERO STACK).
@THIS
D=M
@6
A=D+A
D=M
D=D+M
@SP
A=M-1
M=M-D

// Push temp 6 (510) onto the stack then add (NET ZERO STACK)
@11
D=M
@SP
A=M-1
M=D+M
