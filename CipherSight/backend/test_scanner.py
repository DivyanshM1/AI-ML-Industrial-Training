
import json

from app.scanner.directory_scanner import scan_directory
from app.scanner.report_engine import build_report


# Step 1: Scan the sample project
scan_results = scan_directory("sample_code")

# Step 2: Normalize the results
report = build_report(scan_results)

# Step 3: Display the final JSON report
print("\n========== CIPHERSIGHT SECURITY REPORT ==========\n")

print(json.dumps(report, indent=4))
