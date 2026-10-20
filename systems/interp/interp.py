"""interp.py — a stack-machine interpreter.

Opcodes (the ISA the interpreter executes):
  PUSH n     push constant
  LOAD i     push local i
  STORE i    pop into local i
  ADD        a + b
  SUB        a - b
  MUL        a * b
  DIV        a / b
  DUP        duplicate top
  SWAP       swap top two
  PRINT      pop and print
  JMP a      jump to a
  JZ a       jump if top zero
  JNZ a      jump if top nonzero
  HALT       stop
"""

from __future__ import annotations
import sys


def run(program: list, locals: list = None, trace: bool = False):
    stack = []
    locals = list(locals or [])
    pc = 0
    steps = 0
    while pc < len(program):
        op = program[pc]
        if trace:
            print(f"  {pc:4d}  {op}  stack={stack}")
        if isinstance(op, int):
            stack.append(op)
        elif isinstance(op, str):
            if op == "ADD":
                b, a = stack.pop(), stack.pop()
                stack.append(a + b)
            elif op == "SUB":
                b, a = stack.pop(), stack.pop()
                stack.append(a - b)
            elif op == "MUL":
                b, a = stack.pop(), stack.pop()
                stack.append(a * b)
            elif op == "DIV":
                b, a = stack.pop(), stack.pop()
                stack.append(a // b)
            elif op == "DUP":
                stack.append(stack[-1])
            elif op == "SWAP":
                stack[-1], stack[-2] = stack[-2], stack[-1]
            elif op == "PRINT":
                print(stack.pop())
            elif op == "HALT":
                return stack
            elif op.startswith("LOAD"):
                _, i = op.split(":")
                stack.append(locals[int(i)])
            elif op.startswith("STORE"):
                _, i = op.split(":")
                locals[int(i)] = stack.pop()
            elif op.startswith("JMP:"):
                pc = int(op.split(":")[1]) - 1
            elif op.startswith("JZ:"):
                pc = int(op.split(":")[1]) - 1 if stack.pop() == 0 else pc
            elif op.startswith("JNZ:"):
                pc = int(op.split(":")[1]) - 1 if stack.pop() != 0 else pc
        pc += 1
        steps += 1
        if steps > 1_000_000:
            raise RuntimeError("interpreter: step limit")
    return stack


if __name__ == "__main__":
    demo = [10, 20, "ADD", "PRINT", 5, "MUL", "PRINT", "HALT"]
    print(f"program: {demo}")
    result = run(demo, trace=True)
    print(f"final stack: {result}")
    print("self-test OK")
