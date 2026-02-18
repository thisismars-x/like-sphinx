import os
from pathlib import Path
from structure import extract_structure
import html

def esc(s): return html.escape(str(s)) if s else ""

def render_signature(item):
    '''Render function signature with annotations, defaults, and return type.'''

    args = []
    for a in item.get("args", []):
        part = a["name"]
        if a["annotation"]: part += f": {a['annotation']}"
        if a["default"]:    part += f" = {a['default']}"
        args.append(part)

    sig = f"{item['name']}({', '.join(args)})"
    if item.get("returns"): sig += f" → {item['returns']}"
    return sig

def render_codeblock(code):
    '''Render professional code block with copy button.'''

    return f"""
    <div class="code-block">
        <button class="copy-btn" onclick="copyCode(this)">📋</button>
        <pre><code>{esc(code)}</code></pre>
    </div>
    """

def render_doc(docstring, anchor_id):
    '''Render docstring with doctest detection and anchors.'''

    if not docstring: return ""
    lines = docstring.splitlines(keepends=True)
    html_parts, code_lines = [], []
    in_code = False

    for line in lines:
        if line.lstrip().startswith(">>>"):
            if not in_code:
                in_code = True
                code_lines = []
            code_lines.append(line.rstrip("\n"))
        else:
            if in_code:
                html_parts.append(render_codeblock("\n".join(code_lines)))
                in_code = False

            html_parts.append(esc(line.rstrip("\n")))

    if in_code: html_parts.append(render_codeblock("\n".join(code_lines)))

    return '<div id="{}">'.format(anchor_id) + "<br>\n".join(html_parts) + "</div>"

def render_item(item, index=0, filename="file.py"):
    '''Render class/function with clickable header to file viewer.'''

    anchor_id = f"doc_{index}"
    children_html = ""
    idx_counter = index + 1
    for c in item.get("children", []):
        children_html_part, idx_counter = render_item(c, idx_counter, filename)
        children_html += children_html_part

    span = item.get("span", {})
    line_no = span.get("start_line", 1)

    # Header links directly to file viewer at that line
    header_text = f"class {item['name']}" if item["type"]=="class" else render_signature(item)
    filename = '_'.join(filename.split('/'))
    header_html = f'<a href="{filename}.py_viewer.html#L{line_no}" class="clickable-header">{esc(header_text)}</a>'

    doc_html = render_doc(item['doc'], anchor_id)
    return (
        f"""
        <div class="item">
            <div class="header">{header_html}</div>
            <div class="meta">Lines {span.get('start_line')}–{span.get('end_line')}</div>
            {doc_html}
        </div>
        """,
        idx_counter
    )

def build_docs_html(filename="file.py", remove_py_extensions=True):
    ''' Builds the front page '''

    project_name = os.getcwd().split('/')[-1]

    data = extract_structure(filename)
    if data is None: return # no docs
    if remove_py_extensions and filename.endswith(".py"): filename = filename[:-3]
    struct_html = ""
    idx = 0
    for item in data["struct"]:
        html_part, idx = render_item(item, idx, filename)
        struct_html += html_part

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>{project_name}</title>
    <style>
    body {{
        font-family: system-ui, sans-serif;
        background: #0f172a;
        color: #e5e7eb;
        margin: 40px;
    }}
    .header {{ font-weight: bold; color: #38bdf8; margin-top: 12px; font-size: 20px; }}
    .meta {{ font-size: 0.65em; color: #94a3b8; padding: 2px; }}
    .doc {{ margin-top: 6px; line-height: 1.8em; }}
    .code-block {{
        position: relative;
        background: #1e293b;
        padding: 16px;
        margin: 12px 0;
        overflow-x: auto;
        font-family: "Fira Code", monospace;
        font-size: 1em;
        width: 40%;
    }}
    .code-block pre {{
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
        color: #f8fafc;
    }}
    .copy-btn {{
        position: absolute; top: 8px; right: 8px;
        font-size: 0.75em; padding: 4px 8px;
        cursor: pointer;
        background: #2563eb;
        background-color: transparent;
        color: white; border: none; 
    }}
    .copy-btn:hover {{ background: #1d4ed8; }}
    a.clickable-header {{
        text-decoration: none;
        cursor: pointer;
    }}
    a.clickable-header:hover {{
        text-decoration: underline;
        color: #38bdf8;
    }}
    </style>
    </head>
    <body>
    <h1> {filename} </h1>
    {struct_html}

    <script>
    function copyCode(btn) {{
        const code = btn.nextElementSibling.innerText;
        navigator.clipboard.writeText(code).then(() => {{
            btn.innerText = 'Copied!';
            setTimeout(() => btn.innerText = '📋', 1000);
        }});
    }}
    </script>
    </body>
    </html>
    """

def build_file_viewer(filename="file.py"):
    ''' The file viewer, when clicking on an item, open in some line number '''


    source_lines = Path(filename).read_text(encoding="utf-8").splitlines()
    lines_html = []
    for i, line in enumerate(source_lines, start=1):
        lines_html.append(f'<span id="L{i}"><span class="line-num">{i:>4}</span> {esc(line)}</span>')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>Viewer: {filename}</title>
    <style>
    body {{
        font-family: monospace;
        background: #0f172a;
        color: #e5e7eb;
        margin: 20px;
    }}
    h1 {{
        color: #38bdf8;
    }}
    .line-num {{
        display: inline-block;
        width: 40px;
        color: #64748b;
        user-select: none;
    }}
    span[id^="L"]:hover {{
        background-color: #334155;
    }}
    .highlight {{
        background-color: #38bdf8; 
        color: #0f172a;
    }}
    </style>
    <script>
    window.onload = () => {{
        const hash = location.hash;
        if(hash.startsWith("#L")) {{
            const el = document.querySelector(hash);
            if(el){{
                el.scrollIntoView({{behavior:"smooth", block:"center"}});
                el.classList.add("highlight");
                setTimeout(()=>el.classList.remove("highlight"),1500);
            }}
        }}
    }};
    </script>
    </head>
    <body>
    <h3>{filename}</h3>
    <pre>{'<br>'.join(lines_html)}</pre>
    </body>
    </html>
    """
