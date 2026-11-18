"""Minimal KiCad s-expression reader/writer (no external dependencies)."""
import re

class Sym(str):
    """An unquoted atom."""

_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')

def loads(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while True:
        m = _TOKEN.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            done = stack.pop()
            stack[-1].append(done)
        elif m.group(3) is not None:
            stack[-1].append(m.group(3).replace('\\"', '"').replace('\\\\', '\\'))
        else:
            stack[-1].append(Sym(m.group(4)))
        if pos >= n:
            break
    return stack[0][0]

def dumps(node, indent=0):
    if isinstance(node, list):
        simple = all(not isinstance(c, list) for c in node)
        if simple:
            return '(' + ' '.join(dumps(c) for c in node) + ')'
        pad = '\t' * (indent + 1)
        head = []
        rest = list(node)
        while rest and not isinstance(rest[0], list):
            head.append(dumps(rest.pop(0)))
        out = '(' + ' '.join(head)
        for c in rest:
            out += '\n' + pad + dumps(c, indent + 1)
        out += '\n' + '\t' * indent + ')'
        return out
    if isinstance(node, Sym):
        return str(node)
    if isinstance(node, str):
        return '"' + node.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(node, float):
        return ('%.4f' % node).rstrip('0').rstrip('.')
    return str(node)

def find(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]

def first(node, name):
    r = find(node, name)
    return r[0] if r else None
