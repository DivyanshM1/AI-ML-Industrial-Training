
import json
import subprocess
from types import SimpleNamespace

from app.scanner import semgrep_scanner


def test_normalize_semgrep_finding(tmp_path):
    result = {
        "check_id": "python.lang.security.audit.dangerous-eval",
        "path": "sample.py",
        "start": {"line": 12},
        "extra": {
            "severity": "ERROR",
            "message": "Detected dangerous eval usage.",
            "lines": "eval(user_input)",
            "metadata": {
                "category": "security",
                "confidence": "HIGH",
                "references": ["https://example.com/rule"],
                "cwe": ["CWE-95"],
            },
        },
    }

    finding = semgrep_scanner.normalize_finding(result, tmp_path)

    assert finding["rule_id"].startswith("SEMGREP:")
    assert finding["severity"] == "HIGH"
    assert finding["file"] == "sample.py"
    assert finding["line"] == 12
    assert finding["source"] == "Semgrep"
    assert finding["confidence"] == "HIGH"
    assert finding["cwe"] == ["CWE-95"]


def test_semgrep_scan_parses_json(tmp_path, monkeypatch):
    payload = {
        "results": [
            {
                "check_id": "test.rule",
                "path": "example.py",
                "start": {"line": 4},
                "extra": {
                    "severity": "WARNING",
                    "message": "Test security finding.",
                    "lines": "dangerous_call()",
                    "metadata": {},
                },
            }
        ],
        "paths": {
            "scanned": ["example.py"],
        },
    }

    monkeypatch.setattr(
        semgrep_scanner.shutil,
        "which",
        lambda _: "semgrep",
    )

    monkeypatch.setattr(
        semgrep_scanner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout=json.dumps(payload),
            stderr="",
            returncode=0,
        ),
    )

    result = semgrep_scanner.scan_with_semgrep(tmp_path)

    assert result["status"] == "completed"
    assert len(result["findings"]) == 1
    assert result["findings"][0]["severity"] == "MEDIUM"
    assert result["scanned_paths"] == ["example.py"]
    assert result["errors"] == []


def test_semgrep_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(
        semgrep_scanner.shutil,
        "which",
        lambda _: None,
    )

    result = semgrep_scanner.scan_with_semgrep(tmp_path)

    assert result["status"] == "unavailable"
    assert result["findings"] == []
    assert len(result["errors"]) == 1


def test_semgrep_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr(
        semgrep_scanner.shutil,
        "which",
        lambda _: "semgrep",
    )

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="semgrep",
            timeout=300,
        )

    monkeypatch.setattr(
        semgrep_scanner.subprocess,
        "run",
        raise_timeout,
    )

    result = semgrep_scanner.scan_with_semgrep(tmp_path)

    assert result["status"] == "failed"
    assert result["findings"] == []
    assert "time limit" in result["errors"][0]["error"]


def test_semgrep_invalid_json(tmp_path, monkeypatch):
    monkeypatch.setattr(
        semgrep_scanner.shutil,
        "which",
        lambda _: "semgrep",
    )

    monkeypatch.setattr(
        semgrep_scanner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="not-json",
            stderr="Semgrep execution failed",
            returncode=2,
        ),
    )

    result = semgrep_scanner.scan_with_semgrep(tmp_path)

    assert result["status"] == "failed"
    assert result["findings"] == []
    assert "Semgrep execution failed" in result["errors"][0]["error"]
