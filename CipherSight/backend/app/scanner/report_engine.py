
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import PurePosixPath


SEVERITY_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}

RISK_LABELS = {
    0: "CLEAN",
    1: "LOW",
    2: "MODERATE",
    3: "HIGH",
    4: "CRITICAL",
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


def _clean_text(value, default=""):
    if value is None or isinstance(value, bool):
        return default
    return str(value).strip() or default


def _normalize_path(value):
    path = str(value or "Unknown").replace("\\", "/")
    normalized = str(PurePosixPath(path))

    # If an absolute path appears, retain its project-relative suffix.
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        normalized = PurePosixPath(normalized).name

    return normalized


def _normalize_sources(item):
    sources = item.get("sources")

    if isinstance(sources, list):
        result = [str(source) for source in sources if source]
    else:
        source = item.get("source")
        result = [str(source)] if source else []

    return list(dict.fromkeys(result))


def _normalize_remediation(finding):
    for candidate in (
        finding.get("remediation"),
        finding.get("fix"),
    ):
        value = _clean_text(candidate)
        if value and value.lower() not in INVALID_REMEDIATIONS:
            return value

    return (
        "Review the affected code and apply the secure coding guidance "
        "for this vulnerability. Validate the change with a new scan."
    )


def _finding_identity(finding):
    file_path = _normalize_path(finding.get("file"))
    line = finding.get("line")

    evidence = re.sub(
        r"\s+",
        " ",
        _clean_text(finding.get("evidence")).lower(),
    )

    if evidence:
        return file_path, line, evidence

    description = re.sub(
        r"\s+",
        " ",
        _clean_text(finding.get("description")).lower(),
    )

    return file_path, line, description


def _merge_findings(findings):
    merged = []
    locations = {}

    for original in findings:
        if not isinstance(original, dict):
            continue

        finding = dict(original)
        finding["file"] = _normalize_path(finding.get("file"))
        finding["severity"] = str(
            finding.get("severity", "MEDIUM")
        ).upper()

        if finding["severity"] not in SEVERITY_ORDER:
            finding["severity"] = "MEDIUM"

        sources = _normalize_sources(finding)
        identity = _finding_identity(finding)
        existing_index = locations.get(identity)

        if existing_index is None:
            finding["sources"] = sources
            finding["source"] = ", ".join(sources) or "Unknown"
            finding["remediation"] = _normalize_remediation(finding)
            finding["rule_ids"] = (
                [finding["rule_id"]] if finding.get("rule_id") else []
            )
            locations[identity] = len(merged)
            merged.append(finding)
            continue

        existing = merged[existing_index]
        existing_sources = existing["sources"]

        if not any(source not in existing_sources for source in sources):
            finding["sources"] = sources
            finding["source"] = ", ".join(sources) or "Unknown"
            finding["remediation"] = _normalize_remediation(finding)
            finding["rule_ids"] = (
                [finding["rule_id"]] if finding.get("rule_id") else []
            )
            merged.append(finding)
            continue

        for source in sources:
            if source not in existing_sources:
                existing_sources.append(source)

        existing["source"] = ", ".join(existing_sources)

        incoming_severity = finding["severity"]
        if (
            SEVERITY_ORDER[incoming_severity]
            > SEVERITY_ORDER[existing["severity"]]
        ):
            existing["severity"] = incoming_severity

        generic_categories = {
            "",
            "security",
            "static analysis",
            "uncategorized",
        }

        current_category = _clean_text(existing.get("category"))
        incoming_category = _clean_text(finding.get("category"))

        if (
            current_category.lower() in generic_categories
            and incoming_category.lower() not in generic_categories
        ):
            existing["category"] = incoming_category

        if not existing.get("evidence") and finding.get("evidence"):
            existing["evidence"] = finding["evidence"]

        if (
            len(_clean_text(finding.get("description")))
            > len(_clean_text(existing.get("description")))
        ):
            existing["description"] = finding["description"]

        if (
            _clean_text(existing.get("remediation")).lower()
            in INVALID_REMEDIATIONS
        ):
            existing["remediation"] = _normalize_remediation(finding)

        for rule_id in finding.get("rule_ids", [finding.get("rule_id")]):
            if rule_id and rule_id not in existing["rule_ids"]:
                existing["rule_ids"].append(rule_id)

        if (
            finding.get("rule_id")
            and finding["rule_id"] not in existing["rule_ids"]
        ):
            existing["rule_ids"].append(finding["rule_id"])

        for field in ("confidence", "references", "cwe", "owasp"):
            incoming = finding.get(field)
            if incoming is None:
                continue

            current = existing.get(field)

            if isinstance(incoming, list):
                combined = list(current) if isinstance(current, list) else []
                for item in incoming:
                    if item not in combined:
                        combined.append(item)
                existing[field] = combined
            elif current is None:
                existing[field] = incoming

    return merged


def _normalize_error(error):
    if isinstance(error, str):
        return {
            "file": "Unknown",
            "error": error,
            "sources": [],
        }

    if not isinstance(error, dict):
        return {
            "file": "Unknown",
            "error": str(error),
            "sources": [],
        }

    file_path = _normalize_path(error.get("file", "Unknown"))
    message = _clean_text(error.get("error"), "Unknown scanning error.")

    sources = _normalize_sources(error)

    if not sources and error.get("source"):
        sources = [str(error["source"])]

    # Recover a filename from legacy Semgrep diagnostics if necessary.
    if file_path.lower() in {"semgrep", "unknown"}:
        match = re.search(
            r"([A-Za-z0-9_./\\-]+\.py):\s*(?:Syntax error|Line)",
            message,
            flags=re.IGNORECASE,
        )
        if match:
            file_path = _normalize_path(match.group(1))

    return {
        "file": file_path,
        "error": message,
        "sources": sources,
    }


def _error_identity(error):
    file_path = error["file"].lower()
    message = error["error"].lower()

    if (
        "syntax" in message
        or "unexpected" in message
        or "was never closed" in message
    ):
        return file_path, "syntax"

    normalized_message = re.sub(r"\s+", " ", message)
    return file_path, normalized_message


def _merge_errors(errors):
    merged = []
    locations = {}

    for raw_error in errors:
        error = _normalize_error(raw_error)
        identity = _error_identity(error)

        existing_index = locations.get(identity)

        if existing_index is None:
            locations[identity] = len(merged)
            merged.append(error)
            continue

        existing = merged[existing_index]

        for source in error["sources"]:
            if source not in existing["sources"]:
                existing["sources"].append(source)

        # Keep the more descriptive diagnostic when both engines report it.
        if len(error["error"]) > len(existing["error"]):
            existing["error"] = error["error"]

    return merged


def build_report(scan_results: dict) -> dict:
    raw_findings = scan_results.get("findings", [])
    raw_errors = scan_results.get("errors", [])

    normalized_findings = _merge_findings(raw_findings)
    normalized_errors = _merge_errors(raw_errors)

    severity_counts = Counter()
    category_counts = Counter()
    source_counts = Counter()
    affected_files = set()

    for finding in normalized_findings:
        severity_counts[finding["severity"]] += 1
        category_counts[finding.get("category", "Uncategorized")] += 1
        affected_files.add(finding["file"])

        for source in finding["sources"]:
            source_counts[source] += 1

    highest_severity_score = max(
        (
            SEVERITY_ORDER.get(finding["severity"], 0)
            for finding in normalized_findings
        ),
        default=0,
    )

    highest_severity = next(
        (
            severity
            for severity, score in SEVERITY_ORDER.items()
            if score == highest_severity_score
        ),
        "NONE",
    )

    return {
        "report_version": "1.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": scan_results.get("project", "Unknown"),
        "risk_assessment": {
            "risk_level": RISK_LABELS[highest_severity_score],
            "highest_severity": highest_severity,
        },
        "summary": {
            "files_scanned": scan_results.get("scanned_files", 0),
            "files_skipped": scan_results.get("skipped_files", 0),
            "files_with_findings": len(affected_files),
            "total_findings": len(normalized_findings),
            "total_errors": len(normalized_errors),
        },
        "severity_distribution": {
            severity: severity_counts.get(severity, 0)
            for severity in SEVERITY_ORDER
        },
        "category_distribution": dict(category_counts),
        "source_distribution": dict(source_counts),
        "engines": scan_results.get("engines", {}),
        "findings": normalized_findings,
        "errors": normalized_errors,
    }
