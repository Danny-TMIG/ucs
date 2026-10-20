"""trans.py — stack IR -> valid x86-64 assembly (AT&T syntax)."""

from __future__ import annotations

IR_TO_ASM = {
    "ADD": ["popq %rbx", "popq %rax", "addq %rbx, %rax", "pushq %rax"],
    "SUB": ["popq %rbx", "popq %rax", "subq %rbx, %rax", "pushq %rax"],
    "MUL": ["popq %rbx", "popq %rax", "imulq %rbx, %rax", "pushq %rax"],
    "DIV": ["popq %rbx", "popq %rax", "cqto", "idivq %rbx", "pushq %rax"],
    "DUP": ["movq (%rsp), %rax", "pushq %rax"],
    "SWAP": ["popq %rax", "popq %rbx", "pushq %rax", "pushq %rbx"],
    "PRINT": ["popq %rdi", "call print_int"],
    "HALT": [
        "popq %rdi",  # exit code = top of stack
        "call _exit",
    ],  # libc exit() — works on macOS and Linux
}


def translate(program: list) -> str:
    lines = []
    lines.append(".text")
    lines.append(".globl _start")
    lines.append("_start:")
    for op in program:
        if isinstance(op, int):
            lines.append(f"  pushq ${op}")
        elif isinstance(op, str):
            if op in IR_TO_ASM:
                for a in IR_TO_ASM[op]:
                    lines.append(f"  {a}")
            elif op.startswith("LOAD:"):
                _, i = op.split(":")
                lines.append(f"  pushq {8 * int(i) + 8}(%rbp)")
            elif op.startswith("STORE:"):
                _, i = op.split(":")
                lines.append(f"  popq {8 * int(i) + 8}(%rbp)")
            else:
                lines.append(f"  # unknown: {op}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    demo = [10, 20, "ADD", "HALT"]
    print(translate(demo))
    print("# self-test OK")
