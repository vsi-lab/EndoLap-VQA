"""
Combine 45s video chunks into longer videos as specified by IDs in JSON files.

ID format requiring combination: <serial_no>_45sec_part_<n1>_<n2>_...
  e.g. nephrectomy_342_45sec_part_17_18_19  ->  combines part17, part18, part19

IDs with a single part (e.g. _45sec_part20 or _90sec_part14) are skipped.

Usage:
    python combine_video_chunks.py --chunks /path/to/chunks --output /path/to/combined \
        --json video_chatgpt_training_future.json [more.json ...]
"""

import argparse
import json
import os
import re
import subprocess
import tempfile


MULTI_PART_RE = re.compile(r"^(.+_45sec)_part_(\d+(?:_\d+)+)$")


def parse_id(video_id):
    """Return (base, [part_numbers]) if multi-part, else None."""
    m = MULTI_PART_RE.match(video_id)
    if not m:
        return None
    base = m.group(1)          # e.g. nephrectomy_342_45sec
    parts = [int(p) for p in m.group(2).split("_")]
    return base, parts


def collect_ids(json_files):
    ids = set()
    for path in json_files:
        with open(path) as f:
            for entry in json.load(f):
                ids.add(entry["id"])
    return ids


def combine(video_id, chunks_dir, output_dir):
    parsed = parse_id(video_id)
    if parsed is None:
        return  # single-part id, nothing to combine

    base, parts = parsed
    out_path = os.path.join(output_dir, f"{video_id}.mp4")
    if os.path.exists(out_path):
        print(f"[SKIP] {video_id} already exists.")
        return

    chunk_paths = [os.path.join(chunks_dir, f"{base}_part{p}.mp4") for p in parts]
    missing = [p for p in chunk_paths if not os.path.exists(p)]
    if missing:
        print(f"[WARN] Missing chunks for {video_id}: {missing}")
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as lst:
        lst.write("\n".join(f"file '{p}'" for p in chunk_paths) + "\n")
        list_file = lst.name

    try:
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
               "-i", list_file, "-c", "copy", out_path]
        print(f"[COMBINE] {video_id}  ({len(parts)} parts)")
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            print(f"[ERROR] {video_id}\n{result.stderr.decode()}")
        else:
            print(f"[DONE] {out_path}")
    finally:
        os.unlink(list_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", required=True, help="Directory with 45s chunk .mp4 files")
    parser.add_argument("--output", required=True, help="Directory to save combined videos")
    parser.add_argument("--json", nargs="+", required=True, help="JSON files containing video IDs")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    ids = collect_ids(args.json)
    multi = [vid for vid in ids if parse_id(vid) is not None]
    print(f"[INFO] {len(ids)} unique IDs, {len(multi)} require combining.")

    for vid in sorted(multi):
        combine(vid, args.chunks, args.output)


if __name__ == "__main__":
    main()
