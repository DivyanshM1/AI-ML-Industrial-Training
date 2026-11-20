
import ast
from pathlib import Path
from typing import Any


RULES = {
    "CS001": {
        "category": "Code Injection",
        "severity": "HIGH",
        "description": (
            "Use of eval() can execute dynamically supplied expressions."
        ),
        "remediation": (
            "Avoid eval(). Use safer alternatives such as explicit parsing."
        ),
    },
    "CS002": {
        "category": "Code Injection",
        "severity": "HIGH",
        "description": (
            "Use of exec() can execute dynamically supplied code."
        ),
        "remediation": (
            "Avoid exec(). Use predefined functions or safer execution designs."
        ),
    },
    "CS003": {
        "category": "Command Injection Risk",
        "severity": "HIGH",
        "description": "Subprocess is called with shell=True.",
        "remediation": (
            "Prefer passing commands as a list with shell=False."
        ),
    },
    "CS004": {
        "category": "Insecure Deserialization",
        "severity": "HIGH",
        "description": (
            "Pickle deserialization can execute malicious code "
            "when processing untrusted data."
        ),
        "remediation": (
            "Never deserialize untrusted data with pickle. "
            "Use a safer data format such as JSON."
        ),
    },
    "CS005": {
        "category": "Insecure Deserialization",
        "severity": "HIGH",
        "description": (
            "YAML loading uses a loader that is not recognized as safe."
        ),
        "remediation": (
            "Use yaml.safe_load() or explicitly use yaml.SafeLoader."
        ),
    },
    "CS006": {
        "category": "Insecure TLS Configuration",
        "severity": "MEDIUM",
        "description": (
            "HTTP request or client disables TLS certificate verification."
        ),
        "remediation": (
            "Keep TLS certificate verification enabled. Remove verify=False."
        ),
    },
}


SUBPROCESS_FUNCTIONS = {
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
}

PICKLE_FUNCTIONS = {
    "pickle.load",
    "pickle.loads",
}

YAML_UNSAFE_FUNCTIONS = {
    "yaml.load",
    "yaml.unsafe_load",
}

YAML_SAFE_LOADERS = {
    "yaml.SafeLoader",
    "yaml.CSafeLoader",
}

HTTP_REQUEST_FUNCTIONS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "request",
}

HTTP_CLIENT_CONSTRUCTORS = {
    "requests.Session",
    "httpx.Client",
    "httpx.AsyncClient",
}


def get_call_name(node: ast.AST) -> str | None:
    """Return the dotted name represented by an AST name or attribute."""
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = get_call_name(node.value)

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    return None


class SecurityScanner(ast.NodeVisitor):
    """
    Static security scanner for Python source code.

    Detects selected dangerous API patterns using Python's AST.
    Import aliases are resolved before calls are analyzed.
    """

    def __init__(self, source_code: str, file_path: str):
        self.source_code = source_code
        self.file_path = str(file_path)
        self.source_lines = source_code.splitlines()
        self.findings: list[dict[str, Any]] = []

        self.module_aliases: dict[str, str] = {}
        self.symbol_aliases: dict[str, str] = {}

    def collect_import_aliases(self, tree: ast.Module) -> None:
        """
        Build mappings for imported modules and imported symbols.

        Examples:
            import pickle as p
            p.loads(data) -> pickle.loads(data)

            from pickle import loads as deserialize
            deserialize(data) -> pickle.loads(data)
        """
        for node in ast.walk(tree):

            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        local_name = alias.asname
                        original_name = alias.name
                    else:
                        # `import package.submodule` binds `package`.
                        local_name = alias.name.split(".")[0]
                        original_name = local_name

                    self.module_aliases[local_name] = original_name

            elif isinstance(node, ast.ImportFrom):
                if not node.module:
                    continue

                for alias in node.names:
                    if alias.name == "*":
                        continue

                    local_name = alias.asname or alias.name
                    original_name = f"{node.module}.{alias.name}"

                    self.symbol_aliases[local_name] = original_name

    def resolve_name(self, node: ast.AST) -> str | None:
        """Resolve a call or symbol through known import aliases."""
        name = get_call_name(node)

        if not name:
            return None

        if name in self.symbol_aliases:
            return self.symbol_aliases[name]

        parts = name.split(".")
        original_module = self.module_aliases.get(parts[0], parts[0])

        return ".".join([original_module, *parts[1:]])

    def add_finding(self, node: ast.AST, rule_id: str) -> None:
        """Add a normalized security finding."""
        rule = RULES[rule_id]
        line_number = getattr(node, "lineno", 1)

        evidence = ""
        if 1 <= line_number <= len(self.source_lines):
            evidence = self.source_lines[line_number - 1].strip()

        self.findings.append({
            "rule_id": rule_id,
            "category": rule["category"],
            "severity": rule["severity"],
            "file": self.file_path,
            "line": line_number,
            "evidence": evidence,
            "description": rule["description"],
            "remediation": rule["remediation"],
        })

    def has_keyword(self, node: ast.Call, name: str, value: Any) -> bool:
        """Check whether a call has a keyword with a specific literal value."""
        return any(
            keyword.arg == name
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is value
            for keyword in node.keywords
        )

    def is_safe_yaml_loader(self, node: ast.Call) -> bool:
        """Recognize explicitly imported or qualified safe YAML loaders."""
        loader_node = None

        for keyword in node.keywords:
            if keyword.arg == "Loader":
                loader_node = keyword.value
                break

        # PyYAML also accepts Loader as the second positional argument.
        if loader_node is None and len(node.args) >= 2:
            loader_node = node.args[1]

        if loader_node is None:
            return False

        return self.resolve_name(loader_node) in YAML_SAFE_LOADERS

    def is_http_request(self, call_name: str | None) -> bool:
        """Identify supported requests and httpx request functions."""
        if not call_name:
            return False

        parts = call_name.split(".")

        if len(parts) < 2:
            return False

        module_name = parts[0]
        function_name = parts[-1]

        return (
            module_name in {"requests", "httpx"}
            and function_name in HTTP_REQUEST_FUNCTIONS
        )

    def visit_Module(self, node: ast.Module) -> None:
        self.collect_import_aliases(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        call_name = self.resolve_name(node.func)

        # CS001: Dynamic expression execution.
        if call_name in {"eval", "builtins.eval"}:
            self.add_finding(node, "CS001")

        # CS002: Dynamic code execution.
        elif call_name in {"exec", "builtins.exec"}:
            self.add_finding(node, "CS002")

        # CS003: Shell execution through subprocess.
        elif (
            call_name in SUBPROCESS_FUNCTIONS
            and self.has_keyword(node, "shell", True)
        ):
            self.add_finding(node, "CS003")

        # CS004: Pickle deserialization.
        elif call_name in PICKLE_FUNCTIONS:
            self.add_finding(node, "CS004")

        # CS005: YAML deserialization without a recognized safe loader.
        elif call_name in YAML_UNSAFE_FUNCTIONS:
            if not self.is_safe_yaml_loader(node):
                self.add_finding(node, "CS005")

        # CS006: Disabled TLS certificate verification.
        elif (
            self.is_http_request(call_name)
            or call_name in HTTP_CLIENT_CONSTRUCTORS
        ):
            if self.has_keyword(node, "verify", False):
                self.add_finding(node, "CS006")

        self.generic_visit(node)


def scan_python_file(file_path: str | Path) -> list[dict]:
    """
    Scan a Python file and return security findings.

    Syntax errors are allowed to propagate so the directory scanner
    can record them as file-level scan errors.
    """
    path = Path(file_path)
    source_code = path.read_text(encoding="utf-8")

    syntax_tree = ast.parse(
        source_code,
        filename=str(path),
    )

    scanner = SecurityScanner(
        source_code=source_code,
        file_path=str(path),
    )

    scanner.visit(syntax_tree)

    return scanner.findings
