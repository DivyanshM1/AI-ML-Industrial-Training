
import os
import re
from pathlib import Path

from app.scanner.python_ast import scan_python_file
from app.scanner.semgrep_scanner import scan_with_semgrep


EXCLUDED_DIRECTORIES = {
    "venv",
    ".venv",
    "__pycache__",
    "node_modules",
    ".git",
    ".idea",
    ".vscode",
    "dist",
    "build",
}

MAX_FILE_SIZE = 1_000_000  # 1 MB


def sanitize_diagnostic_message(message: str, root: Path) -> str:
    """Remove the temporary extraction root from scanner diagnostics."""
    cleaned = str(message)
    root_text = str(root.resolve())

    # Handle both Windows and POSIX representations of the project root.
    root_variants = {
        root_text,
        root_text.replace("\\", "/"),
        root.as_posix(),
    }

    for root_variant in sorted(root_variants, key=len, reverse=True):
        if root_variant:
            cleaned = re.sub(
                re.escape(root_variant),
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

    # Normalize path separators after removing the absolute root.
    cleaned = cleaned.replace("\\", "/")

    # Remove leading separators left behind by root removal.
    cleaned = re.sub(
        r"(?<![A-Za-z0-9])/(?:sample_code|[^ ]+\.py)",
        lambda match: match.group(0).lstrip("/"),
        cleaned,
    )

    return cleaned.strip()


def scan_directory(directory_path: str | Path) -> dict:
    root = Path(directory_path).resolve()

    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    findings = []
    errors = []
    scanned_paths = set()
    skipped_files = 0

    # Engine 1: Custom Python AST scanner.
    for current_root, directories, files in os.walk(
        root,
        followlinks=False,
    ):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory.lower() not in EXCLUDED_DIRECTORIES
        )

        for filename in sorted(files):
            if not filename.lower().endswith(".py"):
                continue

            file_path = Path(current_root) / filename
            relative_path = file_path.relative_to(root).as_posix()

            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    skipped_files += 1
                    errors.append({
                        "file": relative_path,
                        "error": (
                            "Python AST scan skipped: "
                            "file exceeds the 1 MB limit."
                        ),
                        "source": "Python AST",
                    })
                    continue

                file_findings = scan_python_file(file_path)

                for finding in file_findings:
                    finding["file"] = relative_path
                    finding["source"] = "Python AST"

                findings.extend(file_findings)
                scanned_paths.add(relative_path)

            except SyntaxError as error:
                errors.append({
                    "file": relative_path,
                    "error": (
                        f"Syntax error at line {error.lineno}: {error.msg}"
                    ),
                    "source": "Python AST",
                })

            except (OSError, UnicodeError) as error:
                errors.append({
                    "file": relative_path,
                    "error": str(error),
                    "source": "Python AST",
                })

    # Engine 2: Semgrep scans the project using its security ruleset.
    semgrep_results = scan_with_semgrep(root)

    findings.extend(semgrep_results.get("findings", []))

    for error in semgrep_results.get("errors", []):
        if isinstance(error, dict):
            normalized_error = dict(error)
            normalized_error.setdefault("source", "Semgrep")

            if "error" in normalized_error:
                normalized_error["error"] = sanitize_diagnostic_message(
                    normalized_error["error"],
                    root,
                )

            errors.append(normalized_error)

        else:
            errors.append({
                "file": "Semgrep",
                "error": sanitize_diagnostic_message(error, root),
                "source": "Semgrep",
            })

    scanned_paths.update(semgrep_results.get("scanned_paths", []))

    return {
        "project": root.name,
        "scanned_files": len(scanned_paths),
        "skipped_files": skipped_files,
        "total_findings": len(findings),
        "findings": findings,
        "errors": errors,
        "engines": {
            "python_ast": "completed",
            "semgrep": semgrep_results.get("status", "unknown"),
        },
    }
