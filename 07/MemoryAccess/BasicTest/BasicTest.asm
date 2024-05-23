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
@LCL
A=M
D=M
@SP
M=M+1
A=M-1
M=D

// Push that 5 (42) onto the stack
@THAT
D=M
@5
A=D+A
D=M
@SP
M=M+1
A=M-1
M=D


// Add top two stack values (local 0 + that 5)
@SP
AM=M-1
D=M
A=A-1
M=M+D

// Push argument 1 (21) onto the stack
@ARG
A=M+1
D=M
@SP
M=M+1
A=M-1
M=D

// Subtract argument 1 from (local 0 + that 5)
@SP
AM=M-1
D=M
A=A-1
M=M-D

// Push this 6 (36) onto the stack
@THIS
D=M
@6
A=D+A
D=M
@SP
M=M+1
A=M-1
M=D


// Push this 6 (36) again onto the stack
@THIS
D=M
@6
A=D+A
D=M
@SP
M=M+1
A=M-1
M=D
M=D+M

// Add the top two stack values (this 6 + this 6)
@SP
AM=M-1
D=M
A=A-1
M=M+D

// Subtract the next two stack values ((local 0 + that 5 - argument 1) - (this 6 + this 6))
@SP
AM=M-1
D=M
A=A-1
M=M-D

// Push temp 6 (510) onto the stack
@11
D=M
@SP
M=M+1
A=M-1
M=D


// Add the final two stack values ((local 0 + that 5 - argument 1) - (this 6 + this 6) + temp 6)
@SP
AM=M-1
D=M
A=A-1
M=M+D
