import json
import csv
import os
import sys
from pathlib import Path

CWD = Path(os.getcwd())

CSV_MAP_FILE = "checkout-checkov-mapping-updates/checkov_map.csv"

BLOCKING_SEVERITIES = {"HIGH", "CRITICAL"}

def load_severity_map(csv_path):
    mapping = {}
    if not os.path.exists(csv_path):
        print(f"Checkov CSV file {csv_path} not found")
        return {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue

            rule_id = row[0].strip()
            severity_text = row[1].strip().upper()
            mapping[rule_id] = severity_text

    print(f"Loaded {len(mapping)} rules from Checkov CSV file")
    return mapping

def _is_finding(result):
    """A SARIF result with no 'kind' defaults to 'fail' per the SARIF spec."""
    return result.get("kind", "fail") == "fail"

def _describe_location(result):
    locations = result.get("locations") or []
    if not locations:
        return "unknown location"

    physical = locations[0].get("physicalLocation", {})
    uri = physical.get("artifactLocation", {}).get("uri", "unknown file")
    start_line = physical.get("region", {}).get("startLine")

    return f"{uri}:{start_line}" if start_line else uri

def evaluate_dir(dir_name, severity_map, soft_fail_on):
    sarif_path = CWD / dir_name / "results_enriched.sarif"

    if not sarif_path.exists():
        print(f"SARIF file {sarif_path} not found, skipping")
        return []

    with open(sarif_path, 'r', encoding='utf-8') as f:
        sarif_data = json.load(f)

    blocking = []

    for run in sarif_data.get("runs", []):
        for result in run.get("results", []):
            if not _is_finding(result):
                continue

            rule_id = result.get("ruleId")
            if not rule_id:
                continue

            severity = severity_map.get(rule_id)
            location = _describe_location(result)

            if severity is None:
                print(f"Blocking (severity unknown - not in map file): {rule_id} at {location}")
                blocking.append((rule_id, severity, location))
                continue

            if severity not in BLOCKING_SEVERITIES:
                print(f"Allowed (severity={severity}, below HIGH/CRITICAL threshold): {rule_id} at {location}")
                continue

            if rule_id in soft_fail_on:
                print(f"Allowed (soft_fail_on override, severity={severity}): {rule_id} at {location}")
                continue

            blocking.append((rule_id, severity, location))

    return blocking

def main():
    severity_map = load_severity_map(CSV_MAP_FILE)

    soft_fail_on = {
        check_id.strip()
        for check_id in os.environ.get("SOFT_FAIL_ON", "").split(",")
        if check_id.strip()
    }

    dirs_env = os.environ.get("SARIF_DIRS", "results.sarif")
    target_dirs = [d.strip() for d in dirs_env.split(",") if d.strip()]

    print(f"Evaluating {len(target_dirs)} directories against severity gate: {target_dirs}")
    print(f"Repo-scoped soft_fail_on overrides (for HIGH/CRITICAL findings only): {sorted(soft_fail_on) or 'none'}")

    all_blocking = []
    for dir_name in target_dirs:
        all_blocking.extend(evaluate_dir(dir_name, severity_map, soft_fail_on))

    if not all_blocking:
        print("No blocking findings. All checks passed or were within accepted severity thresholds.")
        return

    print(f"\n{len(all_blocking)} blocking finding(s):")
    for rule_id, severity, location in all_blocking:
        print(f" - {rule_id} (severity={severity or 'unknown'}) at {location}")

    sys.exit(1)

if __name__ == "__main__":
    main()
