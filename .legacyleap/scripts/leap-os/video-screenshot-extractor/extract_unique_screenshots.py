#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


CONDA_PREREQUISITE_HELP = """Recommended fresh-machine setup:

  conda create -n legacyleap-video python=3.11 -y
  conda activate legacyleap-video
  conda install -c conda-forge ffmpeg pillow -y

Then rerun:

  .legacyleap/scripts/leap-os/video-screenshot-extractor/run.sh
"""

try:
    from PIL import Image, ImageChops, ImageDraw, ImageStat
except ImportError as exc:  # pragma: no cover - exercised by runtime environment
    raise SystemExit(
        "ERROR: Python package Pillow is required.\n\n" + CONDA_PREREQUISITE_HELP
    ) from exc


SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
DEFAULT_SAMPLE_FPS = 1.0
DEFAULT_HASH_THRESHOLD = 10
DEFAULT_MAE_THRESHOLD = 1.25


@dataclass(frozen=True)
class VideoInfo:
    path: Path
    width: int
    height: int
    duration: float
    fps: float


@dataclass(frozen=True)
class CropSpec:
    label: str
    x: int
    y: int
    width: int
    height: int
    reason: str

    @property
    def ffmpeg_value(self) -> str:
        return f"{self.width}:{self.height}:{self.x}:{self.y}"


@dataclass
class Signature:
    dhash: int
    thumb: Image.Image


def run_command(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"ERROR: Required tool not found on PATH: {name}\n\n{CONDA_PREREQUISITE_HELP}")


def repo_root() -> Path:
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".legacyleap").is_dir() and (candidate / "leap-os").is_dir():
            return candidate
    raise SystemExit("ERROR: Run this command from inside a repository with .legacyleap/ and leap-os/.")


def parse_fps(rate: str | None) -> float:
    if not rate or rate == "0/0":
        return 0.0
    if "/" in rate:
        numerator, denominator = rate.split("/", 1)
        den = float(denominator)
        return float(numerator) / den if den else 0.0
    return float(rate)


def probe_video(path: Path) -> VideoInfo:
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,avg_frame_rate,r_frame_rate,duration",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    payload = json.loads(result.stdout)
    stream = payload["streams"][0]
    duration = float(stream.get("duration") or payload.get("format", {}).get("duration") or 0.0)
    fps = parse_fps(stream.get("avg_frame_rate")) or parse_fps(stream.get("r_frame_rate"))
    return VideoInfo(
        path=path,
        width=int(stream["width"]),
        height=int(stream["height"]),
        duration=duration,
        fps=fps,
    )


def discover_videos(videos_dir: Path, requested_video: str | None) -> list[Path]:
    if requested_video:
        video_path = Path(requested_video)
        if not video_path.is_absolute():
            video_path = (Path.cwd() / video_path).resolve()
        if not video_path.exists():
            raise SystemExit(f"ERROR: Requested video does not exist: {video_path}")
        if video_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise SystemExit(f"ERROR: Unsupported video extension: {video_path}")
        return [video_path]

    videos_dir.mkdir(parents=True, exist_ok=True)
    return sorted(
        path
        for path in videos_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def slugify(value: str, used: set[str]) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    slug = slug[:120].strip("-") or "video"
    base = slug
    suffix = 2
    while slug in used:
        slug = f"{base}-{suffix}"
        suffix += 1
    used.add(slug)
    return slug


def format_timestamp(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours:02d}-{minutes:02d}-{secs:02d}"


def sample_times(duration: float) -> list[float]:
    if duration <= 0:
        return [0.0]
    candidates = [
        min(60.0, duration * 0.10),
        duration * 0.25,
        duration * 0.50,
        duration * 0.75,
        max(0.0, duration - min(60.0, duration * 0.10)),
    ]
    cleaned: list[float] = []
    for value in candidates:
        bounded = max(0.0, min(duration - 0.1, value))
        if not any(abs(bounded - existing) < 1.0 for existing in cleaned):
            cleaned.append(bounded)
    return cleaned or [0.0]


def extract_frame(video_path: Path, timestamp: float, output_path: Path) -> None:
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(output_path),
        ]
    )


def sample_video_frames(info: VideoInfo, sample_dir: Path) -> list[Path]:
    sample_dir.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    for index, timestamp in enumerate(sample_times(info.duration), start=1):
        output_path = sample_dir / f"sample_{index:02d}_{format_timestamp(timestamp)}.png"
        extract_frame(info.path, timestamp, output_path)
        frames.append(output_path)
    return frames


def contiguous_runs(indices: list[int]) -> list[tuple[int, int]]:
    if not indices:
        return []
    runs: list[tuple[int, int]] = []
    start = previous = indices[0]
    for index in indices[1:]:
        if index == previous + 1:
            previous = index
            continue
        runs.append((start, previous))
        start = previous = index
    runs.append((start, previous))
    return runs


def snap_crop(spec: CropSpec, video_width: int, video_height: int) -> CropSpec:
    x = max(0, min(spec.x, video_width - 2))
    y = max(0, min(spec.y, video_height - 2))
    width = max(2, min(spec.width, video_width - x))
    height = max(2, min(spec.height, video_height - y))
    if width % 2:
        width -= 1
    if height % 2:
        height -= 1
    return CropSpec(spec.label, x, y, width, height, spec.reason)


def detect_content_bounds(sample_paths: list[Path], video_width: int, video_height: int) -> tuple[int, int, int, int]:
    scale = 4
    small_width = max(1, video_width // scale)
    small_height = max(1, video_height // scale)
    column_scores = [0.0] * small_width
    row_scores = [0.0] * small_height

    for path in sample_paths:
        with Image.open(path) as image:
            small = image.convert("RGB").resize((small_width, small_height), Image.Resampling.BILINEAR)
            pixels = small.load()
            col_counts = [0] * small_width
            row_counts = [0] * small_height
            for y in range(small_height):
                for x in range(small_width):
                    red, green, blue = pixels[x, y]
                    if max(red, green, blue) > 24:
                        col_counts[x] += 1
                        row_counts[y] += 1
            for x, count in enumerate(col_counts):
                column_scores[x] += count / small_height
            for y, count in enumerate(row_counts):
                row_scores[y] += count / small_width

    sample_count = max(1, len(sample_paths))
    column_scores = [score / sample_count for score in column_scores]
    row_scores = [score / sample_count for score in row_scores]

    content_columns = [index for index, score in enumerate(column_scores) if score >= 0.32]
    content_rows = [index for index, score in enumerate(row_scores) if score >= 0.25]
    column_runs = contiguous_runs(content_columns)
    row_runs = contiguous_runs(content_rows)
    if not column_runs or not row_runs:
        return 0, 0, video_width, video_height

    plausible_column_runs = [run for run in column_runs if run[0] <= small_width * 0.20]
    selected_column_run = max(plausible_column_runs or column_runs, key=lambda run: run[1] - run[0])
    selected_row_run = max(row_runs, key=lambda run: run[1] - run[0])

    x0 = max(0, selected_column_run[0] * scale)
    x1 = min(video_width, (selected_column_run[1] + 1) * scale)
    y0 = max(0, selected_row_run[0] * scale)
    y1 = min(video_height, (selected_row_run[1] + 1) * scale)
    return x0, y0, x1, y1


def detect_taskbar_top(sample_paths: list[Path], bounds: tuple[int, int, int, int]) -> int | None:
    x0, y0, x1, y1 = bounds
    width = max(1, x1 - x0)
    detected_tops: list[int] = []
    minimum_block = 8

    for path in sample_paths:
        with Image.open(path) as image:
            region = image.convert("RGB").crop((x0, y0, x1, y1))
            pixels = region.load()
            dark_fractions: list[float] = []
            for local_y in range(region.height):
                dark = 0
                for x in range(region.width):
                    red, green, blue = pixels[x, local_y]
                    brightness = (red + green + blue) / 3
                    if brightness < 80:
                        dark += 1
                dark_fractions.append(dark / width)

        run_length = 0
        run_start: int | None = None
        search_start = int(len(dark_fractions) * 0.65)
        for local_y in range(len(dark_fractions) - 1, search_start, -1):
            if dark_fractions[local_y] >= 0.35:
                run_length += 1
                run_start = local_y
            else:
                if run_length >= minimum_block and run_start is not None:
                    detected_tops.append(y0 + run_start)
                    break
                run_length = 0
                run_start = None
        if run_length >= minimum_block and run_start is not None:
            detected_tops.append(y0 + run_start)

    if not detected_tops:
        return None
    return min(detected_tops)


def suggest_crops(info: VideoInfo, sample_paths: list[Path]) -> list[CropSpec]:
    x0, y0, x1, y1 = detect_content_bounds(sample_paths, info.width, info.height)
    taskbar_top = detect_taskbar_top(sample_paths, (x0, y0, x1, y1))
    suggestions: list[CropSpec] = []

    no_taskbar_bottom = taskbar_top if taskbar_top and taskbar_top > y0 + 100 else y1
    suggestions.append(
        snap_crop(
            CropSpec(
                "auto_application_no_taskbar",
                x0,
                y0,
                x1 - x0,
                no_taskbar_bottom - y0,
                "Detected the main shared desktop region and trimmed the dark Windows taskbar.",
            ),
            info.width,
            info.height,
        )
    )

    suggestions.append(
        snap_crop(
            CropSpec(
                "auto_desktop_with_taskbar",
                x0,
                y0,
                x1 - x0,
                y1 - y0,
                "Detected the main shared desktop region but keeps the Windows taskbar for comparison.",
            ),
            info.width,
            info.height,
        )
    )

    if info.width == 1920 and info.height == 1080:
        suggestions.append(
            CropSpec(
                "known_google_meet_1920x1080_no_taskbar",
                1,
                77,
                1438,
                890,
                "Known crop validated for 1920x1080 Google Meet recordings of this desktop app.",
            )
        )

    unique: list[CropSpec] = []
    seen: set[str] = set()
    for suggestion in suggestions:
        key = suggestion.ffmpeg_value
        if key not in seen:
            unique.append(suggestion)
            seen.add(key)
    return unique


def create_crop_preview(sample_paths: list[Path], suggestions: list[CropSpec], output_path: Path) -> None:
    preview_width = 420
    label_height = 44
    gutter = 12
    cells: list[Image.Image] = []

    for suggestion in suggestions:
        for sample_path in sample_paths[:3]:
            with Image.open(sample_path) as image:
                cropped = image.crop(
                    (
                        suggestion.x,
                        suggestion.y,
                        suggestion.x + suggestion.width,
                        suggestion.y + suggestion.height,
                    )
                )
                ratio = preview_width / cropped.width
                preview_height = max(1, int(cropped.height * ratio))
                preview = cropped.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
                cell = Image.new("RGB", (preview_width, preview_height + label_height), "white")
                cell.paste(preview, (0, label_height))
                draw = ImageDraw.Draw(cell)
                draw.text((6, 5), suggestion.label, fill=(0, 0, 0))
                draw.text((6, 22), f"crop={suggestion.ffmpeg_value}", fill=(64, 64, 64))
                cells.append(cell)

    if not cells:
        return

    columns = min(3, len(cells))
    rows = math.ceil(len(cells) / columns)
    cell_width = max(cell.width for cell in cells)
    cell_height = max(cell.height for cell in cells)
    sheet = Image.new(
        "RGB",
        (
            columns * cell_width + (columns - 1) * gutter,
            rows * cell_height + (rows - 1) * gutter,
        ),
        (235, 235, 235),
    )
    for index, cell in enumerate(cells):
        row = index // columns
        column = index % columns
        sheet.paste(cell, (column * (cell_width + gutter), row * (cell_height + gutter)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def parse_crop(value: str, label: str = "manual") -> CropSpec:
    match = re.fullmatch(r"\s*(\d+):(\d+):(\d+):(\d+)\s*", value)
    if not match:
        raise ValueError("Crop must use ffmpeg format width:height:x:y, for example 1438:890:1:77")
    width, height, x, y = [int(part) for part in match.groups()]
    return CropSpec(label, x, y, width, height, "Manual crop supplied by user.")


def choose_crop(
    info: VideoInfo,
    suggestions: list[CropSpec],
    preview_path: Path,
    *,
    forced_crop: CropSpec | None,
    auto_crop: bool,
    previous_crop: CropSpec | None,
) -> CropSpec:
    if forced_crop is not None:
        return snap_crop(forced_crop, info.width, info.height)
    if auto_crop or not sys.stdin.isatty():
        chosen = suggestions[0]
        print(f"Using crop automatically for {info.path.name}: {chosen.ffmpeg_value} ({chosen.label})")
        return chosen

    print()
    print(f"Crop suggestions for: {info.path.name}")
    print(f"Preview contact sheet: {preview_path}")
    for index, suggestion in enumerate(suggestions, start=1):
        print(f"  {index}. {suggestion.label}: crop={suggestion.ffmpeg_value}")
        print(f"     {suggestion.reason}")
    if previous_crop is not None:
        print(f"  p. Reuse previous crop: crop={previous_crop.ffmpeg_value}")
    print("  m. Enter manual crop as width:height:x:y")

    while True:
        choice = input("Choose crop option: ").strip().lower()
        if previous_crop is not None and choice == "p":
            return snap_crop(previous_crop, info.width, info.height)
        if choice == "m":
            manual_value = input("Manual crop: ").strip()
            try:
                return snap_crop(parse_crop(manual_value), info.width, info.height)
            except ValueError as error:
                print(f"Invalid crop: {error}")
                continue
        if choice.isdigit():
            selected_index = int(choice)
            if 1 <= selected_index <= len(suggestions):
                return suggestions[selected_index - 1]
        print("Enter a valid option number, p, or m.")


def dhash(image: Image.Image, hash_size: int = 16) -> int:
    grayscale = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(grayscale.getdata())
    value = 0
    for row in range(hash_size):
        for column in range(hash_size):
            left = pixels[row * (hash_size + 1) + column]
            right = pixels[row * (hash_size + 1) + column + 1]
            value = (value << 1) | int(left > right)
    return value


def hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def signature_for(image_path: Path) -> Signature:
    with Image.open(image_path) as image:
        grayscale = image.convert("L")
        thumb = grayscale.resize((96, 60), Image.Resampling.LANCZOS)
        return Signature(dhash(grayscale), thumb)


def mean_absolute_error(left: Image.Image, right: Image.Image) -> float:
    difference = ImageChops.difference(left, right)
    return float(ImageStat.Stat(difference).mean[0])


def is_duplicate(
    signature: Signature,
    existing_signatures: Iterable[Signature],
    *,
    hash_threshold: int,
    mae_threshold: float,
) -> bool:
    for existing in existing_signatures:
        distance = hamming_distance(signature.dhash, existing.dhash)
        mae = mean_absolute_error(signature.thumb, existing.thumb)
        if mae <= mae_threshold:
            return True
        if distance <= hash_threshold and mae <= mae_threshold * 3:
            return True
    return False


def archive_existing(path: Path, archive_base: Path, label: str) -> None:
    if not path.exists():
        return
    if not any(path.iterdir()):
        path.rmdir()
        return
    destination = archive_base / label / path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(destination))


def prepare_output_dirs(
    rough_root: Path,
    final_root: Path,
    archive_root: Path,
    run_timestamp: str,
    video_slug: str,
) -> tuple[Path, Path]:
    rough_output = rough_root / video_slug
    final_output = final_root / video_slug
    archive_base = archive_root / run_timestamp
    archive_existing(rough_output, archive_base, "rough")
    archive_existing(final_output, archive_base, "final")
    rough_output.mkdir(parents=True, exist_ok=True)
    final_output.mkdir(parents=True, exist_ok=True)
    return rough_output, final_output


def extract_sampled_frames(video_path: Path, crop: CropSpec, fps: float, output_dir: Path) -> list[Path]:
    fps_value = f"{fps:g}"
    output_pattern = output_dir / "frame_%06d.png"
    run_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps_value},crop={crop.ffmpeg_value}",
            str(output_pattern),
        ]
    )
    return sorted(output_dir.glob("frame_*.png"))


def mirror_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def dedupe_frames(
    frame_paths: list[Path],
    rough_output: Path,
    final_output: Path,
    *,
    sample_fps: float,
    hash_threshold: int,
    mae_threshold: float,
) -> int:
    kept_signatures: list[Signature] = []
    kept_count = 0
    for frame_index, frame_path in enumerate(frame_paths, start=1):
        signature = signature_for(frame_path)
        if is_duplicate(
            signature,
            kept_signatures,
            hash_threshold=hash_threshold,
            mae_threshold=mae_threshold,
        ):
            continue

        kept_signatures.append(signature)
        kept_count += 1
        source_seconds = (frame_index - 1) / sample_fps
        output_name = f"{kept_count:04d}_{format_timestamp(source_seconds)}.png"
        rough_path = rough_output / output_name
        final_path = final_output / output_name
        shutil.copy2(frame_path, rough_path)
        mirror_file(rough_path, final_path)

    return kept_count


def short_hash(path: Path) -> str:
    return hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8]


def process_video(
    info: VideoInfo,
    *,
    slug: str,
    rough_root: Path,
    final_root: Path,
    archive_root: Path,
    tmp_root: Path,
    run_timestamp: str,
    args: argparse.Namespace,
    previous_crop: CropSpec | None,
) -> tuple[CropSpec, int, Path, Path]:
    print()
    print(f"Analyzing video: {info.path.name}")
    print(f"  Resolution: {info.width}x{info.height}")
    print(f"  Duration: {format_timestamp(info.duration).replace('-', ':')}")
    print(f"  FPS: {info.fps:g}")

    sample_dir = tmp_root / f"{slug}-{short_hash(info.path)}" / "samples"
    sample_paths = sample_video_frames(info, sample_dir)
    suggestions = suggest_crops(info, sample_paths)
    preview_path = sample_dir.parent / "crop_options.png"
    create_crop_preview(sample_paths, suggestions, preview_path)

    forced_crop = parse_crop(args.crop, "provided_crop") if args.crop else None
    crop = choose_crop(
        info,
        suggestions,
        preview_path,
        forced_crop=forced_crop,
        auto_crop=args.auto_crop,
        previous_crop=previous_crop,
    )
    print(f"Selected crop for {info.path.name}: {crop.ffmpeg_value} ({crop.label})")

    rough_output, final_output = prepare_output_dirs(
        rough_root,
        final_root,
        archive_root,
        run_timestamp,
        slug,
    )

    with tempfile.TemporaryDirectory(prefix=f"{slug}-frames-") as temp_dir:
        frame_dir = Path(temp_dir)
        print(f"Extracting sampled frames at {args.fps:g} fps...")
        frame_paths = extract_sampled_frames(info.path, crop, args.fps, frame_dir)
        print(f"Deduplicating {len(frame_paths)} sampled frames...")
        kept_count = dedupe_frames(
            frame_paths,
            rough_output,
            final_output,
            sample_fps=args.fps,
            hash_threshold=args.hash_threshold,
            mae_threshold=args.mae_threshold,
        )

    print(f"Kept {kept_count} unique screenshots")
    print(f"  Rough: {rough_output}")
    print(f"  Final: {final_output}")
    return crop, kept_count, rough_output, final_output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract unique desktop-application screenshots from videos in leap-os/videos/."
    )
    parser.add_argument("--videos-dir", default="leap-os/videos", help="Directory containing input videos.")
    parser.add_argument("--rough-dir", default="leap-os/screenshots/rough", help="Rough screenshot output root.")
    parser.add_argument("--final-dir", default="leap-os/screenshots/final", help="Final screenshot output root.")
    parser.add_argument("--archive-dir", default="leap-os/screenshots/archive", help="Archive root for previous outputs.")
    parser.add_argument(
        "--tmp-dir",
        default=".legacyleap/.tmp/video-screenshot-extractor",
        help="Temporary crop-preview directory.",
    )
    parser.add_argument("--video", help="Process a single video path instead of every video in --videos-dir.")
    parser.add_argument("--fps", type=float, default=DEFAULT_SAMPLE_FPS, help="Sampling rate in frames per second.")
    parser.add_argument("--crop", help="Use one crop for all videos, in ffmpeg format width:height:x:y.")
    parser.add_argument("--auto-crop", action="store_true", help="Use the top crop suggestion without prompting.")
    parser.add_argument("--hash-threshold", type=int, default=DEFAULT_HASH_THRESHOLD, help="DHash duplicate threshold.")
    parser.add_argument("--mae-threshold", type=float, default=DEFAULT_MAE_THRESHOLD, help="Thumbnail MAE duplicate threshold.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fps <= 0:
        raise SystemExit("ERROR: --fps must be greater than zero.")
    if args.crop:
        try:
            parse_crop(args.crop)
        except ValueError as error:
            raise SystemExit(f"ERROR: {error}") from error

    require_tool("ffmpeg")
    require_tool("ffprobe")

    root = repo_root()
    videos_dir = (root / args.videos_dir).resolve()
    rough_root = (root / args.rough_dir).resolve()
    final_root = (root / args.final_dir).resolve()
    archive_root = (root / args.archive_dir).resolve()
    tmp_root = Path(args.tmp_dir)
    if not tmp_root.is_absolute():
        tmp_root = (root / tmp_root).resolve()

    videos = discover_videos(videos_dir, args.video)
    videos_dir.mkdir(parents=True, exist_ok=True)
    rough_root.mkdir(parents=True, exist_ok=True)
    final_root.mkdir(parents=True, exist_ok=True)
    archive_root.mkdir(parents=True, exist_ok=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    if not videos:
        print(f"No supported videos found in: {videos_dir}")
        print("Add .mp4, .mov, .mkv, or .webm recordings and rerun this command.")
        return 1

    used_slugs: set[str] = set()
    infos = [probe_video(path) for path in videos]
    slugs = [slugify(info.path.stem, used_slugs) for info in infos]
    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    summaries: list[tuple[VideoInfo, int, Path, Path]] = []
    previous_crop: CropSpec | None = None
    for info, slug in zip(infos, slugs):
        selected_crop, kept_count, rough_output, final_output = process_video(
            info,
            slug=slug,
            rough_root=rough_root,
            final_root=final_root,
            archive_root=archive_root,
            tmp_root=tmp_root,
            run_timestamp=run_timestamp,
            args=args,
            previous_crop=previous_crop,
        )
        previous_crop = selected_crop
        summaries.append((info, kept_count, rough_output, final_output))

    print()
    print("Extraction complete")
    for info, kept_count, rough_output, final_output in summaries:
        print(f"- {info.path.name}: {kept_count} unique screenshots")
        print(f"  Rough: {rough_output}")
        print(f"  Final: {final_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
