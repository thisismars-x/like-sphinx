#! /usr/bin/python
import os
from pathlib import Path
from online import build_docs_html, build_file_viewer

project_name = Path.cwd().name
OUTPUT_DIR = Path.home() / "like-sphinx" / "docs" / project_name
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(path: Path):
    '''Convert a path to a safe HTML filename'''
    return "_".join(path.parts) + ".html"

def generate_file_docs(py_file: Path):
    '''Generate docs and file viewer for a single Python file.'''

    rel_path = py_file.relative_to(Path.cwd())
    docs_html = build_docs_html(str(rel_path))
    viewer_html = build_file_viewer(str(rel_path))

    docs_file = OUTPUT_DIR / sanitize_filename(rel_path)
    viewer_file = OUTPUT_DIR / sanitize_filename(rel_path.with_name(rel_path.name + "_viewer"))

    docs_file.write_text(docs_html, encoding="utf-8")
    viewer_file.write_text(viewer_html, encoding="utf-8")

    return docs_file.name, viewer_file.name

def walk_and_generate(base_dir: Path):
    '''Walk directory recursively, generate docs for all Python files.'''
    all_links = []

    for root, _, files in os.walk(base_dir):
        for file in files:
            try:
                if file.endswith(".py"):
                    py_file = Path(root) / file
                    docs_name, viewer_name = generate_file_docs(py_file)
                    rel_path = py_file.relative_to(base_dir)
                    all_links.append((str(rel_path), docs_name, viewer_name))
            except: pass

    return all_links

def build_index(all_links):
    '''Build a main index page linking to all docs.'''

    list_items = ""
    for rel_path, docs_name, _ in all_links:
        list_items += f'<a href="{docs_name}"><li>{rel_path}</li></a>\n'

    project_name = os.getcwd().split('/')[-1]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{project_name}</title>
        <style>
            body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e5e7eb; margin: 40px; }}
            a {{ color: #38bdf8; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            h1 {{ color: #38bdf8; }}
        </style>
    </head>
    <body>
        <h1>{project_name}</h1>
        <ul>
        {list_items}
        </ul>
    </body>
    </html>
    """
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")

import sys, shutil
def main():
    
    if "clean" in sys.argv: # cleanup
        try:
            shutil.rmtree(Path.home() / "like-sphinx" / "docs")
            print(f"Cleaned all generated docs in /like-sphinx/docs")
        finally: return

    from time import perf_counter_ns
    start = perf_counter_ns()
    all_links = walk_and_generate(Path.cwd())
    build_index(all_links)
    end = perf_counter_ns()
    
    if "then_open" in sys.argv:
        import webbrowser
        webbrowser.open(Path(f"{OUTPUT_DIR}/index.html").resolve().as_uri())
    
    fend = perf_counter_ns()
    print(f"like-sphinx ran for {(end - start) / 1e9:.3f} ms. Excluding browser time, total({(fend-start) / 1e9:.3f}ms).")

main()

