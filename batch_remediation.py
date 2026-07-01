from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

from hier_config import WorkflowRemediation, get_hconfig, Platform
from hier_config.exceptions import DuplicateChildError
from hier_config.utils import read_text_from_file


# Matches "non hardened" / "nonharden" / "non_hardened" / "non-harden" etc.
NONHARDENED_RE = re.compile(r"non[\s_\-]*harden(?:ed)?", re.IGNORECASE)
# Matches "hardened" / "harden" (used only once non-hardened ones are ruled out)
HARDENED_RE = re.compile(r"harden(?:ed)?", re.IGNORECASE)


def classify(path: Path) -> Optional[str]:
    """Return 'nonhardened', 'hardened', or None if the file doesn't match."""
    name = path.name
    if NONHARDENED_RE.search(name):
        return "nonhardened"
    if HARDENED_RE.search(name):
        return "hardened"
    return None


def normalize_key(path: Path, kind: str) -> str:
    """Strip the hardened/nonhardened token and normalize the remaining
    filename so equivalent pairs collapse to the same key."""
    stem = path.stem  # drop extension

    if kind == "nonhardened":
        stem = NONHARDENED_RE.sub("", stem)
    else:
        stem = HARDENED_RE.sub("", stem)

    # Normalize: lowercase, collapse any run of non-alphanumeric chars to '_',
    # strip leading/trailing underscores.
    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    stem = stem.strip("_")
    return stem


@dataclass
class ConfigPair:
    nonhardened: Path
    hardened: Path
    match_quality: float  # 1.0 = exact key match, <1.0 = fuzzy match


def find_pairs(configs_dir: Path) -> tuple[list[ConfigPair], list[Path]]:
    """Scan configs_dir for nonhardened/hardened pairs.

    Returns (pairs, unmatched_files).
    """
    nonhardened: dict[str, Path] = {}
    hardened: dict[str, Path] = {}
    skipped: list[Path] = []

    for entry in sorted(configs_dir.iterdir()):
        if not entry.is_file():
            continue
        kind = classify(entry)
        if kind is None:
            skipped.append(entry)
            continue
        key = normalize_key(entry, kind)
        bucket = nonhardened if kind == "nonhardened" else hardened
        if key in bucket:
            print(
                f"Warning: duplicate key '{key}' for {kind} files - "
                f"'{bucket[key].name}' and '{entry.name}'. Keeping the first."
            )
            continue
        bucket[key] = entry

    pairs: list[ConfigPair] = []
    unmatched: list[Path] = []

    remaining_hardened = dict(hardened)

    for key, nh_path in nonhardened.items():
        if key in remaining_hardened:
            pairs.append(ConfigPair(nh_path, remaining_hardened.pop(key), 1.0))
            continue

        # Fuzzy fallback: best similarity match among leftover hardened keys
        best_key, best_score = None, 0.0
        for hkey in remaining_hardened:
            score = SequenceMatcher(None, key, hkey).ratio()
            if score > best_score:
                best_key, best_score = hkey, score

        if best_key is not None and best_score >= 0.6:
            pairs.append(
                ConfigPair(nh_path, remaining_hardened.pop(best_key), best_score)
            )
        else:
            unmatched.append(nh_path)

    unmatched.extend(remaining_hardened.values())
    unmatched.extend(skipped)

    return pairs, unmatched


def find_duplicate_siblings(text: str) -> list[tuple[str, int, int]]:

    lines = text.splitlines()

    def indent(s: str) -> int:
        return len(s) - len(s.lstrip())

    # stack of (indent_level, seen_dict, parent_label)
    seen_stack: list[dict[str, int]] = [{}]
    indent_stack: list[int] = [-1]
    dupes: list[tuple[str, int, int]] = []

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("!"):
            continue
        level = indent(raw)

        while level <= indent_stack[-1] and len(indent_stack) > 1:
            indent_stack.pop()
            seen_stack.pop()

        seen = seen_stack[-1]
        if stripped in seen:
            dupes.append((stripped, seen[stripped], lineno))
        else:
            seen[stripped] = lineno

        indent_stack.append(level)
        seen_stack.append({})

    return dupes


def write_config(config, filepath: Path) -> bool:
    """Write configuration to a file in Cisco-style format."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for line in config.all_children_sorted():
                f.write(f"{line.cisco_style_text()}\n")
        return True
    except IOError as e:
        print(f"  Error writing to {filepath}: {e}")
        return False


def process_pair(pair: ConfigPair, output_root: Path, platform: Platform) -> dict:
    """Generate remediation/rollback/future for one pair, into its own folder."""
    dest_dir = output_root / pair.nonhardened.stem
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProcessing pair -> {dest_dir.name}/")
    print(f"  nonhardened: {pair.nonhardened.name}")
    print(f"  hardened:    {pair.hardened.name}")
    if pair.match_quality < 1.0:
        print(f"  (fuzzy match, confidence={pair.match_quality:.2f} - verify this pairing)")

    try:
        # Copy originals into the destination folder for traceability.
        shutil.copy2(pair.nonhardened, dest_dir / pair.nonhardened.name)
        shutil.copy2(pair.hardened, dest_dir / pair.hardened.name)

        running_text = read_text_from_file(str(pair.nonhardened))
        generated_text = read_text_from_file(str(pair.hardened))

        running = get_hconfig(platform, running_text)
        generated = get_hconfig(platform, generated_text)

        workflow = WorkflowRemediation(running, generated)

        ok = True
        ok &= write_config(workflow.remediation_config, dest_dir / "remediation.txt")
        ok &= write_config(workflow.rollback_config, dest_dir / "rollback.txt")

        try:
            future_config = running.future(workflow.remediation_config)
        except DuplicateChildError as e:
            print(
                f"  Warning: hier_config's experimental future() merge failed "
                f"({e}); using the hardened config as the future-state approximation."
            )
            future_config = generated

        ok &= write_config(future_config, dest_dir / "future.txt")

        if not ok:
            return {"success": False, "dir": str(dest_dir), "error": "write failure"}

        print("  Generated: remediation.txt, rollback.txt, future.txt")
        return {"success": True, "dir": str(dest_dir)}

    except Exception as e:
        print(f"  Error processing pair: {e}")
        # if isinstance(e, DuplicateChildError) or "duplicate section" in str(e).lower():
        #     for label, src_path in (("nonhardened", pair.nonhardened), ("hardened", pair.hardened)):
        #         try:
        #             dupes = find_duplicate_siblings(src_path.read_text(encoding="utf-8"))
        #         except Exception:
        #             dupes = []
        #         if dupes:
        #             print(f"  Possible duplicate sibling lines in {label} file ({src_path.name}):")
        #             for text, first_ln, dup_ln in dupes:
        #                 print(f"    '{text}' first at line {first_ln}, repeated at line {dup_ln}")
        return {"success": False, "dir": str(dest_dir), "error": str(e)}



PLATFORM_CHOICES = {p.name.lower(): p for p in Platform}


def resolve_platform(dir_name: str, default: Platform) -> Optional[Platform]:
    """Map a directory name (e.g. 'CISCO_IOS', 'cisco-ios', 'CISCO_XR')
    to a hier_config Platform by normalizing both sides for comparison.
    Returns `default` (with a warning) if no match is found."""
    norm = re.sub(r"[^a-z0-9]+", "_", dir_name.lower()).strip("_")

    for platform in Platform:
        if re.sub(r"[^a-z0-9]+", "_", platform.name.lower()).strip("_") == norm:
            return platform

    print(
        f"Warning: directory '{dir_name}' does not match any known Platform "
        f"({', '.join(p.name for p in Platform)}). Falling back to {default.name}."
    )
    return default


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--configs-dir", default="running_config",
        help="Directory whose immediate subdirectories are named after platforms "
             "and contain the *nonhardened*/*hardened* config files (default: running_config)",
    )
    parser.add_argument(
        "--output-dir", default="output",
        help="Directory under which per-platform/per-pair folders are created (default: output)",
    )
    parser.add_argument(
        "--default-platform", default="cisco_ios", choices=sorted(PLATFORM_CHOICES),
        help="Fallback hier_config platform used if a subdirectory name doesn't "
             "match a known Platform (default: cisco_ios)",
    )
    args = parser.parse_args()

    configs_dir = Path(args.configs_dir)
    output_root = Path(args.output_dir)

    if not configs_dir.exists() or not configs_dir.is_dir():
        print(f"Error: configs directory '{configs_dir}' does not exist")
        raise SystemExit(1)

    default_platform = PLATFORM_CHOICES[args.default_platform]

    platform_dirs = sorted(d for d in configs_dir.iterdir() if d.is_dir())
    if not platform_dirs:
        print(f"No platform subdirectories found under '{configs_dir}'.")
        raise SystemExit(1)

    output_root.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []
    all_unmatched: list[Path] = []

    for platform_dir in platform_dirs:
        platform = resolve_platform(platform_dir.name, default_platform)
        print(f"\n=== {platform_dir.name} -> Platform.{platform.name} ===")

        pairs, unmatched = find_pairs(platform_dir)
        all_unmatched.extend(unmatched)

        if not pairs:
            print("  No nonhardened/hardened pairs found.")
            continue
        print(f"  Found {len(pairs)} pair(s).")

        dest_root = output_root / platform_dir.name
        results = [process_pair(pair, dest_root, platform) for pair in pairs]
        all_results.extend(results)

    if all_unmatched:
        print("\nUnmatched / skipped files (no pair found):")
        for f in all_unmatched:
            print(f"  {f}")

    succeeded = sum(1 for r in all_results if r["success"])
    failed = len(all_results) - succeeded
    print(f"\nDone. {succeeded} succeeded, {failed} failed, {len(all_unmatched)} unmatched.")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()