
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


SEMGREP_CONFIG = "p/security-audit"
SEMGREP_TIMEOUT_SECONDS = 300

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

SEVERITY_MAP = {
    "INFO": "LOW",
    "WARNING": "MEDIUM",
    "ERROR": "HIGH",
    "CRITICAL": "CRITICAL",
}

INVALID_REMEDIATIONS = {
    "",
    "false",
    "none",
    "null",
    "true",
    "requires login",
    "login required",
}


def normalize_path(file_path: str, root: Path) -> str:
    """Convert a Semgrep path to a project-relative POSIX path."""
    if not file_path:
        return "unknown"

    raw_path = str(file_path).replace("\\", "/")
    root_resolved = root.resolve()
    root_name = root_resolved.name

    if raw_path.startswith(root_name + "/"):
        raw_path = raw_path[len(root_name) + 1:]

    path = Path(raw_path)

    if not path.is_absolute():
        path = root_resolved / path

    try:
        return path.resolve().relative_to(root_resolved).as_posix()
    except (ValueError, OSError):
        return Path(raw_path).name


def normalize_severity(severity: str | None) -> str:
    normalized = str(severity or "WARNING").upper()
    return SEVERITY_MAP.get(normalized, "MEDIUM")


def normalize_remediation(extra: dict, metadata: dict) -> str:
    for candidate in (
        extra.get("fix"),
        metadata.get("fix"),
        metadata.get("remediation"),
    ):
        if isinstance(candidate, str):
            value = candidate.strip()
            if value.lower() not in INVALID_REMEDIATIONS:
                return value

    return (
        "Review the affected code and apply the secure coding guidance "
        "for this vulnerability. Validate the change with a new scan."
    )


def extract_evidence(
    file_path: str,
    start: dict[str, Any],
    end: dict[str, Any],
    root: Path,
    fallback: Any = "",
) -> str:
    """Read the actual source lines associated with a Semgrep finding."""
    relative_path = normalize_path(file_path, root)

    if relative_path != "unknown":
        source_path = root / Path(relative_path)

        try:
            lines = source_path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()

            start_line = max(1, int(start.get("line", 1)))
            end_line = max(start_line, int(end.get("line", start_line)))

            if start_line <= len(lines):
                evidence = "\n".join(
                    lines[start_line - 1:end_line]
                ).strip()

                if evidence:
                    return evidence

        except (OSError, ValueError, TypeError):
            pass

    if isinstance(fallback, str):
        fallback = fallback.strip()
        if fallback and fallback.lower() not in INVALID_REMEDIATIONS:
            return fallback

    return ""


def normalize_finding(
    result: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    """Convert one Semgrep JSON finding into CipherSight format."""
    extra = result.get("extra") or {}
    metadata = extra.get("metadata") or {}
    start = result.get("start") or {}
    end = result.get("end") or {}

    file_path = str(result.get("path", "unknown"))
    references = metadata.get("references", [])

    if isinstance(references, str):
        references = [references]
    elif not isinstance(references, list):
        references = []

    evidence = extract_evidence(
        file_path=file_path,
        start=start,
        end=end,
        root=root,
        fallback=extra.get("lines", ""),
    )

    return {
        "rule_id": f"SEMGREP:{result.get('check_id', 'unknown')}",
        "category": metadata.get("category", "Static Analysis"),
        "severity": normalize_severity(extra.get("severity")),
        "file": normalize_path(file_path, root),
        "line": start.get("line", 1),
        "evidence": evidence,
        "description": extra.get(
            "message",
            "Semgrep detected a potential security issue.",
        ),
        "remediation": normalize_remediation(extra, metadata),
        "source": "Semgrep",
        "confidence": metadata.get("confidence"),
        "references": references,
        "cwe": metadata.get("cwe"),
        "owasp": metadata.get("owasp"),
    }


def normalize_semgrep_error(
    error: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    """Convert a Semgrep JSON diagnostic into a structured error."""
    file_path = error.get("path")
    start = {}

    if not file_path:
        spans = error.get("spans") or []
        if spans and isinstance(spans[0], dict):
            file_path = spans[0].get("file")
            start = spans[0].get("start") or {}

    start = error.get("start") or start

    message = str(
        error.get("message")
        or error.get("long_msg")
        or "Semgrep reported a scanning diagnostic."
    ).strip()

    # Keep the message readable. The filename and line are separate fields.
    message = message.replace("\r\n", "\n").strip()

    if "syntax" in message.lower() or "unexpected" in message.lower():
        message = f"Syntax error detected by Semgrep: {message}"

    normalized_file = (
        normalize_path(str(file_path), root)
        if file_path
        else "Unknown"
    )

    line = start.get("line")
    if line:
        message = f"Line {line}: {message}"

    return {
        "file": normalized_file,
        "error": message,
        "source": "Semgrep",
    }


def build_result(
    findings=None,
    errors=None,
    status="completed",
    scanned_paths=None,
):
    return {
        "findings": findings or [],
        "errors": errors or [],
        "status": status,
        "scanned_paths": scanned_paths or [],
    }


def scan_with_semgrep(directory_path: str | Path) -> dict[str, Any]:
    """Scan a project directory using Semgrep Community Edition."""
    root = Path(directory_path).resolve()

    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    executable = (
        os.environ.get("SEMGREP_PATH")
        or shutil.which("semgrep")
    )

    if not executable:
        return build_result(
            errors=[{
                "file": "Unknown",
                "error": (
                    "Semgrep is not installed or is not available on PATH. "
                    "Install it separately with pipx."
                ),
                "source": "Semgrep",
            }],
            status="unavailable",
        )

    command = [
        executable,
        "scan",
        "--config",
        SEMGREP_CONFIG,
        "--json",
        "--quiet",
        "--metrics=off",
    ]

    for directory in sorted(EXCLUDED_DIRECTORIES):
        command.extend(["--exclude", directory])

    command.append(str(root))

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=SEMGREP_TIMEOUT_SECONDS,
            check=False,
        )

    except subprocess.TimeoutExpired:
        return build_result(
            errors=[{
                "file": "Unknown",
                "error": (
                    f"Semgrep exceeded the "
                    f"{SEMGREP_TIMEOUT_SECONDS}-second time limit."
                ),
                "source": "Semgrep",
            }],
            status="failed",
        )

    except OSError as error:
        return build_result(
            errors=[{
                "file": "Unknown",
                "error": f"Unable to execute Semgrep: {error}",
                "source": "Semgrep",
            }],
            status="failed",
        )

    try:
        output = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        message = completed.stderr.strip() or (
            f"Semgrep returned invalid JSON with exit code "
            f"{completed.returncode}."
        )
        return build_result(
            errors=[{
                "file": "Unknown",
                "error": message,
                "source": "Semgrep",
            }],
            status="failed",
        )

    if not isinstance(output, dict):
        return build_result(
            errors=[{
                "file": "Unknown",
                "error": "Semgrep returned an unexpected JSON structure.",
                "source": "Semgrep",
            }],
            status="failed",
        )

    findings = [
        normalize_finding(result, root)
        for result in output.get("results", [])
        if isinstance(result, dict)
    ]

    paths = output.get("paths") or {}
    raw_scanned_paths = paths.get("scanned", [])

    if not isinstance(raw_scanned_paths, list):
        raw_scanned_paths = []

    scanned_paths = [
        normalize_path(str(path), root)
        for path in raw_scanned_paths
    ]

    errors = [
        normalize_semgrep_error(error, root)
        if isinstance(error, dict)
        else {
            "file": "Unknown",
            "error": str(error),
            "source": "Semgrep",
        }
        for error in (output.get("errors") or [])
    ]

    if completed.returncode not in (0, 1):
        diagnostic = completed.stderr.strip()
        if diagnostic:
            errors.append({
                "file": "Unknown",
                "error": diagnostic,
                "source": "Semgrep",
            })
        elif not errors:
            errors.append({
                "file": "Unknown",
                "error": (
                    f"Semgrep exited with code {completed.returncode}."
                ),
                "source": "Semgrep",
            })

    status = "completed"
    if errors:
        status = "partial" if findings or scanned_paths else "failed"

    return build_result(
        findings=findings,
        errors=errors,
        status=status,
        scanned_paths=scanned_paths,
    )
