
import ast
from pathlib import Path
from typing import Optional

def _fmt(node):
    ''' Annotated types and default values get formatted better '''
    return ast.unparse(node) if node else None


def _span(node):
    return {
        "start_line": getattr(node, "lineno", None),
        "end_line": getattr(node, "end_lineno", None),
    }


def _parse_args(node):
    ''' Extract function signatures, namely name-annotation-defaultValue triplet '''
    args = []

    all_args = (
        node.args.posonlyargs +
        node.args.args +
        node.args.kwonlyargs
    )

    defaults = [None] * (len(all_args) - len(node.args.defaults)) + node.args.defaults
    for arg, default in zip(all_args, defaults):
        args.append({
            "name": arg.arg,
            "annotation": _fmt(arg.annotation),
            "default": _fmt(default),
        })

    if node.args.vararg:
        args.append({
            "name": "*" + node.args.vararg.arg,
            "annotation": _fmt(node.args.vararg.annotation),
            "default": None,
        })
    if node.args.kwarg:
        args.append({
            "name": "**" + node.args.kwarg.arg,
            "annotation": _fmt(node.args.kwarg.annotation),
            "default": None,
        })

    return args


def _walk(node):
    '''
    This is the recursive engine to walk through AST.

    If a class or function has no docstring. Ignore.
    If a class has no docstring, but its methods have. Ignore.
    '''
    items = []

    for child in getattr(node, "body", []):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(child)
            if not doc: continue
            items.append({
                "type": "async_function" if isinstance(child, ast.AsyncFunctionDef) else "function",
                "name": child.name,
                "doc": doc,
                "args": _parse_args(child),
                "returns": _fmt(child.returns),
                "span": _span(child),
                "children": _walk(child),  # only reached if documented
            })
        elif isinstance(child, ast.ClassDef):
            doc = ast.get_docstring(child)
            if not doc: continue  
            items.append({
                "type": "class",
                "name": child.name,
                "doc": doc,
                "bases": [_fmt(b) for b in child.bases],
                "span": _span(child),
                "children": _walk(child),
            })

        elif isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            items.extend(_walk(child))

    return items


def extract_structure(filename: str = "file.py") -> Optional[dict]:
    ''' Extracts structure of the file by walking through it's AST. '''

    if filename.startswith("_"): return None # secret files

    source = Path(filename).read_text(encoding="utf-8")
    tree = ast.parse(source)
    struct = _walk(tree)
    mod_doc = ast.get_docstring(tree)

    if not mod_doc and not struct: return None

    return dict(mod_doc=mod_doc, mod_span=_span(tree), struct=struct)
