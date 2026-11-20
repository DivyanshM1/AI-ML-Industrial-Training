
from app.scanner.report_engine import build_report


def test_report_preserves_existing_structure():
    scan_results = {
        "project": "test-project",
        "scanned_files": 3,
        "skipped_files": 0,
        "findings": [
            {
                "rule_id": "CS001",
                "category": "Code Injection",
                "severity": "HIGH",
                "file": "app.py",
                "line": 5,
                "evidence": "eval(user_input)",
                "description": "Dangerous eval usage.",
                "remediation": "Avoid eval().",
                "source": "Python AST",
            }
        ],
        "errors": [],
    }

    report = build_report(scan_results)

    assert report["project"] == "test-project"
    assert report["summary"]["files_scanned"] == 3
    assert report["summary"]["total_findings"] == 1
    assert report["risk_assessment"]["risk_level"] == "HIGH"


def test_report_combines_ast_and_semgrep_findings():
    scan_results = {
        "project": "combined-project",
        "scanned_files": 5,
        "skipped_files": 0,
        "findings": [
            {
                "rule_id": "CS001",
                "category": "Code Injection",
                "severity": "HIGH",
                "file": "app.py",
                "line": 5,
                "evidence": "eval(user_input)",
                "description": "AST finding.",
                "remediation": "Avoid eval().",
                "source": "Python AST",
            },
            {
                "rule_id": "SEMGREP:test.rule",
                "category": "security",
                "severity": "MEDIUM",
                "file": "app.py",
                "line": 8,
                "evidence": "dangerous_call()",
                "description": "Semgrep finding.",
                "remediation": "Review the call.",
                "source": "Semgrep",
                "confidence": "HIGH",
                "references": ["https://example.com"],
            },
        ],
        "errors": [],
        "engines": {
            "python_ast": "completed",
            "semgrep": "completed",
        },
    }

    report = build_report(scan_results)

    assert report["summary"]["total_findings"] == 2
    assert report["source_distribution"] == {
        "Python AST": 1,
        "Semgrep": 1,
    }
    assert report["engines"]["semgrep"] == "completed"

    semgrep_finding = report["findings"][1]

    assert semgrep_finding["confidence"] == "HIGH"
    assert semgrep_finding["references"] == ["https://example.com"]


def test_report_handles_empty_scan():
    report = build_report({
        "project": "clean-project",
        "scanned_files": 2,
        "skipped_files": 0,
        "findings": [],
        "errors": [],
        "engines": {
            "python_ast": "completed",
            "semgrep": "completed",
        },
    })

    assert report["risk_assessment"]["risk_level"] == "CLEAN"
    assert report["summary"]["total_findings"] == 0
    assert report["severity_distribution"]["HIGH"] == 0
