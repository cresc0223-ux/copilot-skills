#!/usr/bin/env python3
"""Idempotently update a persistent asset usage ledger from a final manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import Counter
from datetime import datetime
from pathlib import Path

from video_common import configure_stdout, load_json, write_json


def counts_from_manifest(path: Path) -> Counter[str]:
    data = load_json(path)
    counts: Counter[str] = Counter()
    for item in data.get("assets", []):
        asset = item.get("path")
        if asset:
            counts[str(Path(asset).resolve())] += int(item.get("usage_count_this_video", 1))
    return counts


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--ledger-dir", required=True, type=Path)
    parser.add_argument("--project-name", default="")
    args = parser.parse_args()

    manifest_bytes = args.manifest.read_bytes()
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    current = counts_from_manifest(args.manifest)
    args.ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = args.ledger_dir / "asset_usage.json"
    ledger = {"schema_version": 1, "assets": {}, "projects": {}}
    if ledger_path.exists():
        try:
            loaded = load_json(ledger_path)
            if isinstance(loaded, dict) and "assets" in loaded:
                ledger = loaded
        except (OSError, ValueError):
            pass

    project = args.project_name or args.manifest.parent.name
    previous = ledger.setdefault("projects", {}).get(project, {})
    if previous.get("manifest_sha256") == digest:
        print(f"ledger already contains unchanged project: {project}")
        return

    assets = ledger.setdefault("assets", {})
    for path, count in previous.get("counts", {}).items():
        if path in assets:
            assets[path]["total_usage_count"] = max(0, int(assets[path].get("total_usage_count", 0)) - int(count))
    now = datetime.now().isoformat(timespec="seconds")
    for path, count in current.items():
        record = assets.setdefault(path, {"path": path, "total_usage_count": 0, "last_used_in": "", "last_used_at": ""})
        record["total_usage_count"] = int(record.get("total_usage_count", 0)) + count
        record["last_used_in"] = project
        record["last_used_at"] = now
    ledger["projects"][project] = {"manifest_sha256": digest, "counts": dict(current), "updated_at": now}
    write_json(ledger_path, ledger)

    csv_path = args.ledger_dir / "asset_usage.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["path", "total_usage_count", "last_used_in", "last_used_at"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in sorted(assets.values(), key=lambda item: item["path"].casefold()):
            writer.writerow(record)
    print(ledger_path)


if __name__ == "__main__":
    main()

