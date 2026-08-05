#!/usr/bin/env python3
"""Scan, classify, and select varied local assets with usage-aware ranking."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from video_common import (
    IMAGE_EXTS,
    MEDIA_EXTS,
    VIDEO_EXTS,
    config_path,
    configure_stdout,
    find_ffmpeg,
    find_ffprobe,
    load_json,
    media_summary,
    write_json,
)


ROLE_HINTS = {
    "detail": ["detail", "close", "macro", "product", "item", "sku", "\u5355\u54c1", "\u7ec6\u8282", "\u7279\u5199", "\u4ea7\u54c1"],
    "context": ["wide", "aisle", "shelf", "room", "venue", "overview", "scene", "\u8d27\u67b6", "\u8d70\u5eca", "\u5168\u666f", "\u73af\u5883", "\u573a\u666f"],
    "location": ["facade", "storefront", "entrance", "exterior", "address", "map", "sign", "\u95e8\u5934", "\u5165\u53e3", "\u5916\u666f", "\u5730\u5740", "\u62db\u724c"],
    "people": ["person", "people", "staff", "customer", "demo", "hand", "model", "\u4eba\u7269", "\u5e97\u5458", "\u987e\u5ba2", "\u6f14\u793a", "\u624b\u90e8"],
    "brand": ["logo", "brand", "title", "packaging", "identity", "\u6807\u5fd7", "\u54c1\u724c", "\u7247\u5934", "\u5305\u88c5"],
}
EXCLUDED_PARTS = {"outputs", "output", "cache", "proxy", "proxies", "thumbs", "thumbnail", "thumbnails", ".git", ".local-short-video"}


def load_usage(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not path.exists():
        return counts
    try:
        data = load_json(path)
    except (OSError, ValueError):
        return counts
    records = data.values() if isinstance(data, dict) else data
    for record in records:
        if isinstance(record, dict) and record.get("path"):
            counts[str(Path(record["path"]).resolve()).casefold()] = int(record.get("total_usage_count", 0))
    return counts


def classify(path: Path) -> str:
    haystack = " ".join(path.parts).casefold()
    scores = {role: sum(1 for hint in hints if hint.casefold() in haystack) for role, hints in ROLE_HINTS.items()}
    role, score = max(scores.items(), key=lambda item: item[1])
    return role if score else "unknown"


def scan(root: Path, category: str, exclude_patterns: list[str]) -> list[Path]:
    category_folded = category.casefold().strip()
    excluded_folded = [pattern.casefold().strip() for pattern in exclude_patterns if pattern.strip()]
    result = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in MEDIA_EXTS:
            continue
        relative_parts = [part.casefold() for part in path.relative_to(root).parts]
        if any(part.startswith(".") or part in EXCLUDED_PARTS for part in relative_parts[:-1]):
            continue
        relative_text = str(path.relative_to(root)).casefold()
        if category_folded and category_folded not in relative_text:
            continue
        if any(pattern in relative_text for pattern in excluded_folded):
            continue
        result.append(path.resolve())
    return result


def choose(records: list[dict], count: int) -> list[dict]:
    role_order = ["detail", "context", "people", "location", "brand", "unknown"]
    pools = {role: [] for role in role_order}
    for record in records:
        pools[record["role"]].append(record)
    for pool in pools.values():
        pool.sort(key=lambda item: (item["historical_usage"], item["kind"] != "video", -item["bytes"], item["path"].casefold()))

    selected: list[dict] = []
    target_mix = ["detail", "context", "detail", "people", "context", "location", "detail", "brand", "unknown"]
    while len(selected) < count and any(pools.values()):
        progressed = False
        for role in target_mix:
            if pools[role] and len(selected) < count:
                selected.append(pools[role].pop(0))
                progressed = True
        if not progressed:
            break
    if len(selected) < count:
        leftovers = [item for pool in pools.values() for item in pool]
        leftovers.sort(key=lambda item: (item["historical_usage"], item["kind"] != "video", -item["bytes"]))
        selected.extend(leftovers[: count - len(selected)])
    for index, record in enumerate(selected, 1):
        record["selection_order"] = index
        duration = float(record.get("duration") or 0)
        record["source_start"] = round(min(max(duration * 0.25, 0.0), max(duration - 1.0, 0.0)), 3) if record["kind"] == "video" else 0
    return selected


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--category", default="")
    parser.add_argument("--exclude", action="append", default=[], help="Exclude paths containing this text; repeat as needed")
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()

    config_file = args.config.resolve()
    config = load_json(config_file)
    root = config_path(config, "materials_root", config_file)
    if not root.is_dir():
        raise SystemExit(f"Materials root not found: {root}")
    ffmpeg = find_ffmpeg(config)
    ffprobe = find_ffprobe(config, ffmpeg)
    ledger_dir = config_path(config, "ledger_dir", config_file, str(config_path(config, "workspace_root", config_file) / ".local-short-video" / "asset_usage"))
    usage = load_usage(ledger_dir / "asset_usage.json")

    paths = scan(root, args.category, args.exclude)
    if not paths:
        raise SystemExit(f"No supported media matched under {root}")
    records = []
    for path in paths:
        stat = path.stat()
        summary = media_summary(path, ffprobe, ffmpeg) if path.suffix.lower() in VIDEO_EXTS else {"duration": 0, "width": 0, "height": 0, "codec": "image", "has_audio": False, "probe_error": ""}
        records.append({
            "path": str(path),
            "relative_path": str(path.relative_to(root)),
            "kind": "video" if path.suffix.lower() in VIDEO_EXTS else "image",
            "role": classify(path),
            "bytes": stat.st_size,
            "historical_usage": usage[str(path).casefold()],
            **summary,
        })
    selected = choose(records, min(args.count, len(records)))
    role_counts = Counter(item["role"] for item in selected)
    manifest = {
        "materials_root": str(root),
        "category_filter": args.category,
        "exclude_patterns": args.exclude,
        "scanned_count": len(records),
        "selection_policy": "role diversity, low historical usage, video preference, file size",
        "role_counts": dict(role_counts),
        "assets": selected,
    }
    out = args.out or config_file.parent / "selected_assets.json"
    csv_path = args.csv or config_file.parent / "selected_assets.csv"
    write_json(out, manifest)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["selection_order", "path", "relative_path", "kind", "role", "duration", "source_start", "historical_usage", "bytes"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(selected)
    print(out)


if __name__ == "__main__":
    main()
