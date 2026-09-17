"""
cg_extract.py — Extractores de entidades y relaciones por lenguaje.

Cada extractor recibe (relpath, source) y devuelve dict {nodes, edges}.
Todo es deterministico: mismo input produce siempre el mismo output.
Sin dependencias externas — Python via modulo ast, resto via regex.

Schema de salida:
  nodes: [{id, label, kind, file_type, source_file, source_location}]
  edges: [{source, target, relation, confidence, confidence_score,
           source_file, source_location}]

Confianza:
  EXTRACTED  — relacion explicita en el codigo (import, call directo, herencia)
  INFERRED   — deducida en el pase de resolucion cross-file (score 0.55-0.95)
  AMBIGUOUS  — incierta, marcada para revision humana (score 0.1-0.3)
"""

import ast
import re
from pathlib import PurePosixPath

# ---------------------------------------------------------------------------
# IDs y utilidades
# ---------------------------------------------------------------------------

_ID_RE = re.compile(r"[^a-z0-9_]+")


def norm_id(text):
    """Normaliza un texto a [a-z0-9_]."""
    return _ID_RE.sub("_", text.lower()).strip("_")


def file_stem_id(relpath):
    """ID base de un archivo: ruta relativa completa sin extension.

    'src/auth/session.py' -> 'src_auth_session'
    Mantiene todos los niveles de directorio para que archivos con el mismo
    nombre en carpetas distintas no colisionen.
    """
    p = PurePosixPath(str(relpath).replace("\\", "/"))
    parts = list(p.parts)
    if parts:
        parts[-1] = p.stem
    return norm_id("_".join(parts))


def entity_id(relpath, name):
    """ID de un simbolo dentro de un archivo: {stem}_{entity}."""
    return f"{file_stem_id(relpath)}_{norm_id(name)}"


def _node(nid, label, kind, file_type, source_file, loc=None):
    return {
        "id": nid,
        "label": label,
        "kind": kind,
        "file_type": file_type,
        "source_file": source_file,
        "source_location": loc,
    }


def _edge(src, tgt, relation, confidence, score, source_file, loc=None):
    return {
        "source": src,
        "target": tgt,
        "relation": relation,
        "confidence": confidence,
        "confidence_score": score,
        "source_file": source_file,
        "source_location": loc,
    }


def _file_node(relpath, file_type):
    name = PurePosixPath(str(relpath).replace("\\", "/")).name
    return _node(file_stem_id(relpath), name, "file", file_type, relpath, "L1")


class Extraction:
    """Acumulador de nodos y edges de un archivo."""

    def __init__(self, relpath, file_type):
        self.relpath = relpath
        self.file_node = _file_node(relpath, file_type)
        self.nodes = [self.file_node]
        self.edges = []
        # llamadas sin resolver: (caller_id, callee_name, line)
        self.pending_calls = []
        # nombres de tipos base sin resolver: (child_id, base_name, line)
        self.pending_bases = []
        # imports sin resolver: (module_string, line)
        self.pending_imports = []
        # simbolos definidos en este archivo: name -> node_id
        self.defs = {}

    def add_symbol(self, name, label, kind, line):
        nid = entity_id(self.relpath, name)
        if name not in self.defs:
            self.defs[name] = nid
            self.nodes.append(
                _node(nid, label, kind, self.file_node["file_type"],
                      self.relpath, f"L{line}")
            )
            self.edges.append(
                _edge(self.file_node["id"], nid, "contains", "EXTRACTED",
                      1.0, self.relpath, f"L{line}")
            )
        return nid

    def result(self):
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "pending_calls": self.pending_calls,
            "pending_bases": self.pending_bases,
            "pending_imports": self.pending_imports,
            "defs": self.defs,
            "relpath": self.relpath,
        }


# ---------------------------------------------------------------------------
# Python — via modulo ast (fidelidad completa)
# ---------------------------------------------------------------------------

def extract_python(relpath, source):
    ex = Extraction(relpath, "code")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ex.result()

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.scope = []  # stack de node_ids (clase/funcion actual)

        def _owner(self):
            return self.scope[-1] if self.scope else ex.file_node["id"]

        def visit_Import(self, node):
            for alias in node.names:
                ex.pending_imports.append((alias.name, node.lineno))
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            mod = ("." * (node.level or 0)) + (node.module or "")
            # 'from pkg import mod' puede referirse a un submodulo: se emite
            # la forma unida 'pkg.mod' que el resolver intenta primero como
            # archivo; si no existe, cae al modulo base.
            for alias in node.names:
                if alias.name == "*":
                    ex.pending_imports.append((mod, node.lineno))
                    continue
                joined = mod + alias.name if mod.endswith(".") \
                    else f"{mod}.{alias.name}"
                ex.pending_imports.append((joined, node.lineno))
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            nid = ex.add_symbol(node.name, node.name, "class", node.lineno)
            for base in node.bases:
                bname = _py_name(base)
                if bname:
                    ex.pending_bases.append((nid, bname, node.lineno))
            self.scope.append(nid)
            self.generic_visit(node)
            self.scope.pop()

        def _visit_func(self, node):
            kind = "method" if any(
                s for s in ex.nodes if s["id"] == self._owner()
                and s["kind"] == "class"
            ) else "function"
            label = node.name + "()"
            nid = ex.add_symbol(node.name, label, kind, node.lineno)
            owner = self._owner()
            if owner != ex.file_node["id"]:
                ex.edges.append(_edge(owner, nid, "contains", "EXTRACTED",
                                      1.0, relpath, f"L{node.lineno}"))
            self.scope.append(nid)
            self.generic_visit(node)
            self.scope.pop()

        visit_FunctionDef = _visit_func
        visit_AsyncFunctionDef = _visit_func

        def visit_Call(self, node):
            callee = _py_name(node.func)
            if callee:
                ex.pending_calls.append(
                    (self._owner(), callee, node.lineno))
            self.generic_visit(node)

    Visitor().visit(tree)
    return ex.result()


def _py_name(node):
    """Nombre plano de una expresion: foo, obj.metodo -> 'metodo'."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


# ---------------------------------------------------------------------------
# Familia regex — definiciones por lenguaje
# ---------------------------------------------------------------------------
#
# Cada spec define patrones para: imports, clases (con herencia), funciones,
# y llamadas. Los patrones capturan nombre y opcionalmente bases.

_CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")

# palabras que parecen llamadas pero son keywords/builtins de control
_CALL_STOPWORDS = {
    "if", "for", "while", "switch", "catch", "return", "function", "func",
    "fun", "def", "match", "when", "until", "elif", "else", "new", "throw",
    "typeof", "sizeof", "assert", "super", "this", "it", "print", "println",
    "printf", "len", "require", "import", "include", "use", "loop", "defer",
    "yield", "await", "async", "in", "is", "not", "and", "or", "do", "try",
    "select", "case", "class", "struct", "enum", "interface", "impl",
    "constructor", "init", "lambda", "foreach", "unless", "given",
}


def _strip_comments(source, line_comment, block=("/*", "*/")):
    """Elimina comentarios preservando numeros de linea."""
    out = []
    in_block = False
    if not block or not block[0]:
        block = None
    for line in source.splitlines():
        if in_block:
            end = line.find(block[1])
            if end >= 0:
                line = " " * (end + len(block[1])) + line[end + len(block[1]):]
                in_block = False
            else:
                out.append("")
                continue
        if block and block[0] in line:
            start = line.find(block[0])
            end = line.find(block[1], start + len(block[0]))
            if end >= 0:
                line = line[:start] + " " * (end + len(block[1]) - start) + line[end + len(block[1]):]
            else:
                line = line[:start]
                in_block = True
        if line_comment:
            idx = line.find(line_comment)
            if idx >= 0:
                line = line[:idx]
        out.append(line)
    return out


def _regex_extract(relpath, source, spec):
    """Extractor generico dirigido por spec."""
    ex = Extraction(relpath, "code")
    lines = _strip_comments(source, spec.get("line_comment"),
                            spec.get("block_comment", ("/*", "*/")))
    current_owner = [ex.file_node["id"]]

    for lineno, line in enumerate(lines, 1):
        for pat in spec.get("imports", []):
            for m in pat.finditer(line):
                ex.pending_imports.append((m.group(1), lineno))

        for pat in spec.get("file_bases", []):
            m = pat.search(line)
            if m:
                ex.pending_bases.append(
                    (ex.file_node["id"], m.group("base"), lineno))

        for pat, kind in spec.get("types", []):
            m = pat.search(line)
            if m:
                name = m.group("name")
                nid = ex.add_symbol(name, name, kind, lineno)
                bases = m.groupdict().get("bases")
                if bases:
                    for b in re.split(r"[,\s]+", bases.strip()):
                        b = b.split("<")[0].split("(")[0].strip()
                        if b and b[0].isalpha():
                            ex.pending_bases.append((nid, b, lineno))
                current_owner = [nid]

        for pat in spec.get("functions", []):
            m = pat.search(line)
            if m:
                name = m.group("name")
                nid = ex.add_symbol(name, name + "()", "function", lineno)
                current_owner = [nid]

        # llamadas: cualquier identificador seguido de '(' que no sea keyword
        for m in _CALL_RE.finditer(line):
            callee = m.group(1)
            if callee in _CALL_STOPWORDS or callee in spec.get("stopwords", ()):
                continue
            # ignorar la propia definicion en esta linea
            if any(p.search(line) and p.search(line).group("name") == callee
                   for p in spec.get("functions", [])):
                continue
            ex.pending_calls.append((current_owner[0], callee, lineno))

    return ex.result()


LANG_SPECS = {
    "javascript": {
        "line_comment": "//",
        "imports": [
            re.compile(r"""import\s+(?:[\w{}\s,*]+\s+from\s+)?['"]([^'"]+)['"]"""),
            re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
            re.compile(r"""import\(\s*['"]([^'"]+)['"]\s*\)"""),
        ],
        "types": [
            (re.compile(r"\bclass\s+(?P<name>[A-Za-z_$][\w$]*)"
                        r"(?:\s+extends\s+(?P<bases>[\w$.]+))?"), "class"),
            (re.compile(r"\binterface\s+(?P<name>[A-Za-z_$][\w$]*)"
                        r"(?:\s+extends\s+(?P<bases>[\w$.,\s]+?))?\s*\{"), "interface"),
        ],
        "functions": [
            re.compile(r"\bfunction\s*\*?\s+(?P<name>[A-Za-z_$][\w$]*)\s*\("),
            re.compile(r"\b(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*=\s*"
                       r"(?:async\s+)?(?:\([^)]*\)|[\w$]+)\s*=>"),
            re.compile(r"^\s*(?:async\s+)?(?P<name>[A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{"),
        ],
        "stopwords": {"useState", "useEffect", "describe", "expect", "test"},
    },
    "kotlin": {
        "line_comment": "//",
        "imports": [re.compile(r"^\s*import\s+([\w.]+)")],
        "types": [
            (re.compile(r"\b(?:data\s+|sealed\s+|abstract\s+|open\s+|enum\s+)*class\s+"
                        r"(?P<name>[A-Za-z_]\w*)"
                        r"(?:[^:{]*:\s*(?P<bases>[\w.<>,\s()]+?))?\s*(?:\{|$)"), "class"),
            (re.compile(r"\binterface\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s*:\s*(?P<bases>[\w.<>,\s]+?))?\s*(?:\{|$)"), "interface"),
            (re.compile(r"\bobject\s+(?P<name>[A-Za-z_]\w*)"), "object"),
        ],
        "functions": [
            re.compile(r"\bfun\s+(?:<[^>]+>\s+)?(?:[\w.<>]+\.)?(?P<name>[A-Za-z_]\w*)\s*\("),
        ],
    },
    "java": {
        "line_comment": "//",
        "imports": [re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+)")],
        "types": [
            (re.compile(r"\b(?:public\s+|abstract\s+|final\s+)*class\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s+extends\s+(?P<bases>[\w.<>]+))?"), "class"),
            (re.compile(r"\binterface\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s+extends\s+(?P<bases>[\w.<>,\s]+?))?\s*\{"), "interface"),
            (re.compile(r"\benum\s+(?P<name>[A-Za-z_]\w*)"), "enum"),
        ],
        "functions": [
            re.compile(r"(?:public|private|protected|static|final|synchronized|abstract)"
                       r"[\w<>\[\],\s]*\s+(?P<name>[a-z]\w*)\s*\([^)]*\)\s*(?:throws[\w,\s]+)?\{"),
        ],
    },
    "csharp": {
        "line_comment": "//",
        "imports": [re.compile(r"^\s*using\s+(?:static\s+)?([\w.]+)\s*;")],
        "types": [
            (re.compile(r"\b(?:public\s+|internal\s+|abstract\s+|sealed\s+|partial\s+|static\s+)*"
                        r"class\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s*:\s*(?P<bases>[\w.<>,\s]+?))?\s*(?:\{|$)"), "class"),
            (re.compile(r"\binterface\s+(?P<name>I[A-Za-z_]\w*)"
                        r"(?:\s*:\s*(?P<bases>[\w.<>,\s]+?))?\s*(?:\{|$)"), "interface"),
            (re.compile(r"\b(?:public\s+|internal\s+)?record\s+(?P<name>[A-Za-z_]\w*)"), "class"),
        ],
        "functions": [
            re.compile(r"(?:public|private|protected|internal|static|async|override|virtual)"
                       r"[\w<>\[\],\s?]*\s+(?P<name>[A-Z]\w*)\s*\([^)]*\)\s*(?:\{|=>)"),
        ],
    },
    "go": {
        "line_comment": "//",
        "imports": [
            re.compile(r"""^\s*(?:import\s+)?(?:[\w.]+\s+)?"([^"]+)"\s*$"""),
        ],
        "types": [
            (re.compile(r"\btype\s+(?P<name>[A-Za-z_]\w*)\s+struct\b"), "class"),
            (re.compile(r"\btype\s+(?P<name>[A-Za-z_]\w*)\s+interface\b"), "interface"),
        ],
        "functions": [
            re.compile(r"\bfunc\s+(?:\([^)]+\)\s+)?(?P<name>[A-Za-z_]\w*)\s*\("),
        ],
    },
    "rust": {
        "line_comment": "//",
        "imports": [re.compile(r"^\s*use\s+([\w:]+)")],
        "types": [
            (re.compile(r"\b(?:pub\s+)?struct\s+(?P<name>[A-Za-z_]\w*)"), "class"),
            (re.compile(r"\b(?:pub\s+)?enum\s+(?P<name>[A-Za-z_]\w*)"), "enum"),
            (re.compile(r"\b(?:pub\s+)?trait\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s*:\s*(?P<bases>[\w+\s]+?))?\s*\{"), "interface"),
            (re.compile(r"\bimpl(?:<[^>]+>)?\s+(?:(?P<bases>[\w:]+)\s+for\s+)?"
                        r"(?P<name>[A-Za-z_]\w*)"), "class"),
        ],
        "functions": [
            re.compile(r"\b(?:pub\s+)?(?:async\s+)?fn\s+(?P<name>[A-Za-z_]\w*)\s*[(<]"),
        ],
    },
    "gdscript": {
        "line_comment": "#",
        "block_comment": ('"""', '"""'),
        "imports": [
            re.compile(r"""preload\(\s*["']([^"']+)["']\s*\)"""),
            re.compile(r"""(?<!pre)load\(\s*["']([^"']+)["']\s*\)"""),
        ],
        "types": [
            (re.compile(r"^\s*class_name\s+(?P<name>[A-Za-z_]\w*)"), "class"),
            (re.compile(r"^\s*class\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s+extends\s+(?P<bases>[\w.]+))?"), "class"),
        ],
        "file_bases": [
            re.compile(r"^\s*extends\s+(?P<base>[A-Za-z_]\w*)\s*$"),
        ],
        "functions": [
            re.compile(r"^\s*(?:static\s+)?func\s+(?P<name>[A-Za-z_]\w*)\s*\("),
        ],
        "stopwords": {"emit_signal", "connect", "get_node", "preload", "load",
                      "export", "onready", "signal"},
    },
    "shell": {
        "line_comment": "#",
        "block_comment": (None, None),
        "imports": [
            re.compile(r"^\s*(?:source|\.)\s+([\w./\-]+)"),
        ],
        "types": [],
        "functions": [
            re.compile(r"^\s*(?:function\s+)?(?P<name>[A-Za-z_][\w\-]*)\s*\(\)\s*\{?"),
            re.compile(r"^\s*function\s+(?P<name>[A-Za-z_][\w\-]*)\b"),
        ],
    },
    "powershell": {
        "line_comment": "#",
        "block_comment": ("<#", "#>"),
        "imports": [
            re.compile(r"""(?i)^\s*\.\s+["']?([\w./\\:\$\{\}\-]+\.ps1)"""),
            re.compile(r"(?i)Import-Module\s+([\w.\-]+)"),
        ],
        "types": [
            (re.compile(r"^\s*class\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s*:\s*(?P<bases>[\w.]+))?"), "class"),
        ],
        "functions": [
            re.compile(r"(?i)^\s*function\s+(?P<name>[\w\-]+)"),
        ],
    },
    "php": {
        "line_comment": "//",
        "imports": [
            re.compile(r"^\s*use\s+([\w\\]+)"),
            re.compile(r"""(?:require|include)(?:_once)?\s*\(?\s*['"]([^'"]+)['"]"""),
        ],
        "types": [
            (re.compile(r"\b(?:abstract\s+|final\s+)?class\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s+extends\s+(?P<bases>[\w\\]+))?"), "class"),
            (re.compile(r"\binterface\s+(?P<name>[A-Za-z_]\w*)"), "interface"),
            (re.compile(r"\btrait\s+(?P<name>[A-Za-z_]\w*)"), "class"),
        ],
        "functions": [
            re.compile(r"\bfunction\s+(?P<name>[A-Za-z_]\w*)\s*\("),
        ],
    },
    "ruby": {
        "line_comment": "#",
        "block_comment": (None, None),
        "imports": [
            re.compile(r"""^\s*require(?:_relative)?\s+['"]([^'"]+)['"]"""),
        ],
        "types": [
            (re.compile(r"^\s*class\s+(?P<name>[A-Z]\w*)"
                        r"(?:\s*<\s*(?P<bases>[\w:]+))?"), "class"),
            (re.compile(r"^\s*module\s+(?P<name>[A-Z]\w*)"), "object"),
        ],
        "functions": [
            re.compile(r"^\s*def\s+(?:self\.)?(?P<name>[\w?!]+)"),
        ],
    },
    "swift": {
        "line_comment": "//",
        "imports": [re.compile(r"^\s*import\s+([\w.]+)")],
        "types": [
            (re.compile(r"\b(?:final\s+|open\s+|public\s+)*class\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s*:\s*(?P<bases>[\w,\s.]+?))?\s*\{"), "class"),
            (re.compile(r"\bstruct\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s*:\s*(?P<bases>[\w,\s.]+?))?\s*\{"), "class"),
            (re.compile(r"\bprotocol\s+(?P<name>[A-Za-z_]\w*)"), "interface"),
            (re.compile(r"\bextension\s+(?P<name>[A-Za-z_]\w*)"), "class"),
            (re.compile(r"\benum\s+(?P<name>[A-Za-z_]\w*)"), "enum"),
        ],
        "functions": [
            re.compile(r"\bfunc\s+(?P<name>[A-Za-z_]\w*)\s*[(<]"),
        ],
    },
    "c": {
        "line_comment": "//",
        "imports": [re.compile(r'^\s*#\s*include\s+[<"]([^>"]+)[>"]')],
        "types": [
            (re.compile(r"\b(?:typedef\s+)?struct\s+(?P<name>[A-Za-z_]\w*)\s*\{"), "class"),
            (re.compile(r"\bclass\s+(?P<name>[A-Za-z_]\w*)"
                        r"(?:\s*:\s*(?:public|private|protected)?\s*(?P<bases>[\w:,\s]+?))?\s*\{"), "class"),
        ],
        "functions": [
            re.compile(r"^[\w*&:<>~\s]+?\b(?P<name>[A-Za-z_]\w*)\s*\([^;)]*\)\s*(?:const)?\s*\{"),
        ],
    },
}

# alias de spec por lenguaje detectado
_SPEC_ALIASES = {
    "typescript": "javascript",
    "cpp": "c",
}


def extract_regex_lang(relpath, source, lang):
    spec = LANG_SPECS[_SPEC_ALIASES.get(lang, lang)]
    return _regex_extract(relpath, source, spec)


# ---------------------------------------------------------------------------
# SQL — tablas, vistas, foreign keys, joins
# ---------------------------------------------------------------------------

_SQL_TABLE = re.compile(r"(?i)\bcreate\s+(?:or\s+replace\s+)?table\s+(?:if\s+not\s+exists\s+)?[`\"\[]?([\w.]+)")
_SQL_VIEW = re.compile(r"(?i)\bcreate\s+(?:or\s+replace\s+)?view\s+[`\"\[]?([\w.]+)")
_SQL_FK = re.compile(r"(?i)\breferences\s+[`\"\[]?([\w.]+)")
_SQL_JOIN = re.compile(r"(?i)\bjoin\s+[`\"\[]?([\w.]+)")
_SQL_FROM = re.compile(r"(?i)\bfrom\s+[`\"\[]?([\w.]+)")


def extract_sql(relpath, source):
    ex = Extraction(relpath, "sql")
    lines = _strip_comments(source, "--")
    current_table = None
    for lineno, line in enumerate(lines, 1):
        m = _SQL_TABLE.search(line)
        if m:
            name = m.group(1).split(".")[-1]
            current_table = ex.add_symbol(name, name, "table", lineno)
            continue
        m = _SQL_VIEW.search(line)
        if m:
            name = m.group(1).split(".")[-1]
            view_id = ex.add_symbol(name, name, "view", lineno)
            current_table = view_id
        for m in _SQL_FK.finditer(line):
            tgt = m.group(1).split(".")[-1]
            if current_table:
                ex.pending_calls.append((current_table, tgt, lineno))
                ex.edges.append(_edge(
                    current_table, entity_id(relpath, tgt), "foreign_key",
                    "EXTRACTED", 1.0, relpath, f"L{lineno}"))
        for pat, rel in ((_SQL_JOIN, "joins"), (_SQL_FROM, "reads_from")):
            for m in pat.finditer(line):
                tgt = m.group(1).split(".")[-1]
                if tgt.lower() in ("select", "dual") or not current_table:
                    continue
                if rel == "joins":
                    ex.pending_bases.append((current_table, tgt, lineno))
    return ex.result()


# ---------------------------------------------------------------------------
# Markdown — headings como conceptos, links y referencias a simbolos
# ---------------------------------------------------------------------------

_MD_HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*#*\s*$")
_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)#\s]+)")
_MD_CODEREF = re.compile(r"`([A-Za-z_][\w./]{2,60})(?:\(\))?`")


def extract_markdown(relpath, source):
    ex = Extraction(relpath, "document")
    ex.file_node["kind"] = "doc"
    in_fence = False
    for lineno, line in enumerate(source.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _MD_HEADING.match(line)
        if m and len(m.group(2)) <= 80:
            title = m.group(2).strip()
            nid = ex.add_symbol(title, title, "concept", lineno)
        for m in _MD_LINK.finditer(line):
            target = m.group(2)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            ex.pending_imports.append((target, lineno))
        for m in _MD_CODEREF.finditer(line):
            ref = m.group(1)
            # solo referencias con pinta de simbolo o archivo
            if "/" in ref or "." in ref or "_" in ref or ref[0].isupper() \
                    or ref.islower() and len(ref) > 4:
                ex.pending_calls.append((ex.file_node["id"], ref.split(".")[-1]
                                         if "/" not in ref else ref, lineno))
    return ex.result()


# ---------------------------------------------------------------------------
# Config (JSON/YAML/TOML) — nodo de archivo + rutas referenciadas
# ---------------------------------------------------------------------------

_CFG_PATHREF = re.compile(r"""["']([\w\-./\\]+\.(?:py|js|ts|sh|ps1|json|ya?ml|md|gd|kt|sql|toml))["']""")


def extract_config(relpath, source):
    ex = Extraction(relpath, "config")
    ex.file_node["kind"] = "config"
    for lineno, line in enumerate(source.splitlines(), 1):
        for m in _CFG_PATHREF.finditer(line):
            ex.pending_imports.append((m.group(1), lineno))
    return ex.result()


# ---------------------------------------------------------------------------
# Dispatch por extension
# ---------------------------------------------------------------------------

EXTENSION_MAP = {
    ".py": ("python", extract_python),
    ".pyw": ("python", extract_python),
    ".js": ("javascript", None),
    ".jsx": ("javascript", None),
    ".mjs": ("javascript", None),
    ".cjs": ("javascript", None),
    ".ts": ("typescript", None),
    ".tsx": ("typescript", None),
    ".kt": ("kotlin", None),
    ".kts": ("kotlin", None),
    ".java": ("java", None),
    ".cs": ("csharp", None),
    ".go": ("go", None),
    ".rs": ("rust", None),
    ".gd": ("gdscript", None),
    ".sh": ("shell", None),
    ".bash": ("shell", None),
    ".zsh": ("shell", None),
    ".ps1": ("powershell", None),
    ".psm1": ("powershell", None),
    ".php": ("php", None),
    ".rb": ("ruby", None),
    ".swift": ("swift", None),
    ".c": ("c", None),
    ".h": ("c", None),
    ".cpp": ("cpp", None),
    ".hpp": ("cpp", None),
    ".cc": ("cpp", None),
    ".sql": ("sql", extract_sql),
    ".md": ("markdown", extract_markdown),
    ".markdown": ("markdown", extract_markdown),
    ".json": ("config", extract_config),
    ".yaml": ("config", extract_config),
    ".yml": ("config", extract_config),
    ".toml": ("config", extract_config),
}


def extract_file(relpath, source):
    """Punto de entrada: despacha al extractor segun extension."""
    ext = PurePosixPath(str(relpath).replace("\\", "/")).suffix.lower()
    entry = EXTENSION_MAP.get(ext)
    if entry is None:
        return None
    lang, fn = entry
    if fn is not None:
        return fn(relpath, source)
    return extract_regex_lang(relpath, source, lang)


def language_of(relpath):
    ext = PurePosixPath(str(relpath).replace("\\", "/")).suffix.lower()
    entry = EXTENSION_MAP.get(ext)
    return entry[0] if entry else None


# ---------------------------------------------------------------------------
# Pase de resolucion cross-file
# ---------------------------------------------------------------------------

def resolve(extractions, all_relpaths):
    """Segundo pase: resuelve llamadas, herencias e imports entre archivos.

    Reglas de confianza:
      - llamada resuelta dentro del mismo archivo        -> EXTRACTED 1.0
      - callee con definicion unica en el mismo lenguaje -> INFERRED 0.95
      - varias definiciones, una en el mismo directorio  -> INFERRED 0.75
      - varias definiciones sin desambiguar              -> se omite (no
        se inventan edges; el reporte cuenta cuantas se descartaron)
    """
    nodes, edges = [], []
    seen_nodes = set()
    seen_edges = set()
    dropped_ambiguous = 0

    # indice global: nombre -> [(node_id, relpath, lang)]
    global_defs = {}
    file_ids = {}  # relpath normalizada -> file node id
    for ext_r in extractions:
        rel = ext_r["relpath"]
        file_ids[_norm_rel(rel)] = file_stem_id(rel)
        lang = language_of(rel)
        for name, nid in ext_r["defs"].items():
            global_defs.setdefault(name, []).append((nid, rel, lang))

    def add_node(n):
        if n["id"] not in seen_nodes:
            seen_nodes.add(n["id"])
            nodes.append(n)

    def add_edge(e):
        key = (e["source"], e["target"], e["relation"])
        if e["source"] != e["target"] and key not in seen_edges:
            seen_edges.add(key)
            edges.append(e)

    for ext_r in extractions:
        for n in ext_r["nodes"]:
            add_node(n)
        for e in ext_r["edges"]:
            add_edge(e)

    for ext_r in extractions:
        rel = ext_r["relpath"]
        lang = language_of(rel)
        rel_dir = str(PurePosixPath(_norm_rel(rel)).parent)

        # --- llamadas ---
        for caller, callee, lineno in ext_r["pending_calls"]:
            if callee in ext_r["defs"]:
                add_edge(_edge(caller, ext_r["defs"][callee], "calls",
                               "EXTRACTED", 1.0, rel, f"L{lineno}"))
                continue
            candidates = [
                (nid, r) for nid, r, lg in global_defs.get(callee, [])
                if lg == lang or lang == "markdown"
            ]
            if len(candidates) == 1:
                relation = "references" if lang == "markdown" else "calls"
                add_edge(_edge(caller, candidates[0][0], relation,
                               "INFERRED", 0.95, rel, f"L{lineno}"))
            elif len(candidates) > 1:
                same_dir = [c for c in candidates
                            if str(PurePosixPath(_norm_rel(c[1])).parent) == rel_dir]
                if len(same_dir) == 1:
                    relation = "references" if lang == "markdown" else "calls"
                    add_edge(_edge(caller, same_dir[0][0], relation,
                                   "INFERRED", 0.75, rel, f"L{lineno}"))
                else:
                    dropped_ambiguous += 1

        # --- herencia / joins ---
        for child, base, lineno in ext_r["pending_bases"]:
            relation = "joins" if language_of(rel) == "sql" else "inherits"
            if base in ext_r["defs"]:
                add_edge(_edge(child, ext_r["defs"][base], relation,
                               "EXTRACTED", 1.0, rel, f"L{lineno}"))
                continue
            candidates = [(nid, r) for nid, r, lg in global_defs.get(base, [])
                          if lg == lang]
            if len(candidates) == 1:
                add_edge(_edge(child, candidates[0][0], relation,
                               "INFERRED", 0.95, rel, f"L{lineno}"))
            elif len(candidates) > 1:
                dropped_ambiguous += 1

        # --- imports ---
        src_file_id = file_stem_id(rel)
        for module, lineno in ext_r["pending_imports"]:
            target_id = _resolve_import(module, rel, file_ids, all_relpaths)
            if target_id:
                add_edge(_edge(src_file_id, target_id, "imports",
                               "EXTRACTED", 1.0, rel, f"L{lineno}"))
            else:
                # modulo externo: nodo compartido, sin ruta
                ext_name = module.lstrip(".").split("/")[0].split("\\")[0]
                base = ext_name.split(".")[0]
                if not base or len(base) < 2:
                    continue
                ext_id = "external_" + norm_id(base)
                add_node(_node(ext_id, base, "external", "external",
                               None, None))
                add_edge(_edge(src_file_id, ext_id, "imports",
                               "EXTRACTED", 1.0, rel, f"L{lineno}"))

    return {"nodes": nodes, "edges": edges,
            "dropped_ambiguous": dropped_ambiguous}


def _norm_rel(rel):
    return str(rel).replace("\\", "/")


_IMPORT_EXTS = ("", ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".gd",
                ".sh", ".ps1", ".md", ".kt", ".java", ".rb", ".php")


def _resolve_import(module, from_rel, file_ids, all_relpaths):
    """Intenta mapear un string de import a un archivo del corpus."""
    from_dir = PurePosixPath(_norm_rel(from_rel)).parent
    mod = _norm_rel(module)
    # esquemas de ruta de proyecto (godot): res://x/y.gd -> x/y.gd
    for scheme in ("res://", "user://"):
        if mod.startswith(scheme):
            mod = mod[len(scheme):]
            break

    # 1. ruta relativa explicita (./x, ../x, x/y.ext)
    if mod.startswith("."):
        # imports relativos python: .mod / ..mod
        if re.match(r"^\.+[\w.]*$", mod) and "/" not in mod:
            dots = len(mod) - len(mod.lstrip("."))
            tail = mod.lstrip(".")
            base = from_dir
            for _ in range(dots - 1):
                base = base.parent
            candidate = str(base / tail.replace(".", "/")) if tail else str(base)
        else:
            candidate = str((from_dir / mod))
        candidate = _collapse(candidate)
        for ext in _IMPORT_EXTS:
            hit = file_ids.get(candidate + ext) or \
                file_ids.get(candidate + "/__init__.py") or \
                file_ids.get(candidate + "/index" + ext if ext else None)
            if hit:
                return hit
        return None

    # 2. python dotted: a.b.c -> a/b/c.py
    if re.match(r"^[\w.]+$", mod) and "." in mod:
        candidate = mod.replace(".", "/")
        for suffix in (".py", "/__init__.py", ".kt", ".java"):
            for known, fid in file_ids.items():
                if known.endswith(candidate + suffix):
                    return fid

    # 3. ruta directa en el corpus (con o sin extension)
    for ext in _IMPORT_EXTS:
        target = _collapse(mod + ext)
        if target in file_ids:
            return file_ids[target]
        # busqueda por sufijo (res:// de godot, rutas absolutas de proyecto)
        matches = [fid for known, fid in file_ids.items()
                   if known.endswith("/" + target) or known == target]
        if len(matches) == 1:
            return matches[0]

    # 4. nombre simple de modulo python del corpus: 'utils' -> utils.py
    if re.match(r"^\w+$", mod):
        matches = [fid for known, fid in file_ids.items()
                   if known.endswith("/" + mod + ".py") or known == mod + ".py"]
        if len(matches) == 1:
            return matches[0]

    return None


def _collapse(path):
    """Normaliza ./ y ../ en una ruta relativa."""
    parts = []
    for p in _norm_rel(path).split("/"):
        if p in ("", "."):
            continue
        if p == "..":
            if parts:
                parts.pop()
            continue
        parts.append(p)
    return "/".join(parts)
