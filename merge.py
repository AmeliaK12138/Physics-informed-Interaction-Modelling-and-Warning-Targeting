"""
Merge 0508 and 0509 raw driving-interaction CSV files on a 0.1 s ego timeline.

Input layout:
    0508/raw_data/HMI_TestID_<subject>_<trial>_<HMI>_<timestamp>/
    0509/raw_data/HMI_TestID_<subject>_<trial>_<HMI>_<timestamp>/
        _VR3_VehicleTrack.csv
        _VR3_Track.csv
        BackGroundManTrack.csv

Output:
    0508/processed_data/<subject>_<trial>_<HMI>.csv
    0509/processed_data/<subject>_<trial>_<HMI>.csv
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from merge_0325 import merge_experiment


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_DIRS = [SCRIPT_DIR / "0508", SCRIPT_DIR / "0509"]
EXPERIMENT_NAME_PATTERN = re.compile(
    r"^HMI_TestID_(?P<subject>[^_]+)_(?P<trial>[^_]+)_(?P<hmi>[A-Za-z])_"
)


def parse_experiment_name(folder_name: str) -> tuple[str, str, str]:
    match = EXPERIMENT_NAME_PATTERN.match(folder_name)
    if not match:
        raise ValueError(f"Unexpected experiment folder name: {folder_name}")
    return match.group("subject"), match.group("trial"), match.group("hmi")


def process_base_dir(base_dir: Path) -> tuple[int, int]:
    raw_dir = base_dir / "raw_data"
    output_dir = base_dir / "processed_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    folders = sorted(path for path in raw_dir.iterdir() if path.is_dir())
    if not folders:
        raise FileNotFoundError(f"No experiment folders found under {raw_dir}")

    print(f"Processing {base_dir.name}: {raw_dir}")
    ok_count = 0
    for folder in folders:
        subject_id, trial_id, hmi_type = parse_experiment_name(folder.name)
        output_file = output_dir / f"{subject_id}_{trial_id}_{hmi_type}.csv"
        try:
            merged = merge_experiment(folder)
        except Exception as exc:
            print(f"[SKIP] {folder.name}: {exc}")
            continue

        merged.to_csv(output_file, index=False, encoding="utf-8-sig")
        ok_count += 1
        print(f"[OK] {folder.name} -> {output_file.name} ({len(merged)} rows)")

    print(f"Done {base_dir.name}. Wrote {ok_count}/{len(folders)} files to {output_dir}")
    return ok_count, len(folders)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-dir",
        dest="base_dirs",
        action="append",
        type=Path,
        help=(
            "Directory containing raw_data and processed_data. "
            "Can be supplied multiple times. Defaults to ./0508 and ./0509 next to this script."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dirs = args.base_dirs or DEFAULT_BASE_DIRS

    total_ok = 0
    total_count = 0
    for base_dir in base_dirs:
        ok_count, folder_count = process_base_dir(base_dir)
        total_ok += ok_count
        total_count += folder_count

    print(f"All done. Wrote {total_ok}/{total_count} files.")


if __name__ == "__main__":
    main()
