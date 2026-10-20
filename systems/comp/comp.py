"""comp.py — a compiler for a tiny expression language.

Grammar:
  expr   := term (('+' | '-') term)*
  term   := atom (('*' | '/') atom)*
  atom   := INT | '(' expr ')'
"""

from __future__ import annotations
import re, sys

TOKEN = re.compile(r"\s*(\d+|\+|-|\*|/|\(|\))")


def lex(text: str) -> list:
    toks, pos = [], 0
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            raise SyntaxError(f"at {pos}: {text[pos : pos + 10]!r}")
        toks.append(m.group(1))
        pos = m.end()
    return toks


def parse(toks: list) -> list:
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def eat(t=None):
        cur = toks[pos[0]]
        pos[0] += 1
        if t and cur != t:
            raise SyntaxError(f"expected {t}, got {cur}")
        return cur

    def expr():
        code = term()
        while peek() in ("+", "-"):
            op = eat()
            rhs = term()
            code += rhs + [{"+": "ADD", "-": "SUB"}[op]]
        return code

    def term():
        code = atom()
        while peek() in ("*", "/"):
            op = eat()
            rhs = atom()
            code += rhs + [{"*": "MUL", "/": "DIV"}[op]]
        return code

    def atom():
        t = peek()
        if t == "(":
            eat()
            code = expr()
            eat(")")
            return code
        return [int(eat())]

    out = expr()
    if pos[0] != len(toks):
        raise SyntaxError(f"trailing tokens at {pos[0]}")
    return out + ["HALT"]


def compile_source(text: str) -> list:
    return parse(lex(text))


if __name__ == "__main__":
    for src in ["1+2", "2*3+4", "(1+2)*3", "10/2-1"]:
        ir = compile_source(src)
        print(f"{src:12s} -> {ir}")
    print("self-test OK")
