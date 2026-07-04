import argparse
import concurrent.futures
import io
import os
from pathlib import Path
from typing import Iterable, Optional, Tuple

from PIL import Image
from rembg import remove

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff", ".tif", ".gif"}


def parse_color(value: str) -> Optional[Tuple[int, int, int]]:
    if not value:
        return None
    parts = value.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("bg-color must be three comma-separated values, e.g. 255,255,255")
    try:
        rgb = tuple(int(p.strip()) for p in parts)
    except ValueError:
        raise argparse.ArgumentTypeError("bg-color values must be integers")
    if any(c < 0 or c > 255 for c in rgb):
        raise argparse.ArgumentTypeError("bg-color values must be between 0 and 255")
    return rgb


def get_input_files(input_path: Path) -> Iterable[Path]:
    if input_path.is_dir():
        return [p for p in sorted(input_path.iterdir()) if p.suffix.lower() in SUPPORTED_EXT]
    if input_path.is_file():
        return [input_path]
    return []


def ensure_output_folder(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)


def save_png(image: Image.Image, output_path: Path, bg_color: Optional[Tuple[int, int, int]]) -> None:
    if bg_color is not None:
        background = Image.new("RGBA", image.size, (*bg_color, 255))
        image = Image.alpha_composite(background, image)
    image.save(output_path, "PNG")


def remove_background(data: bytes, model_name: str, bg_color: Optional[Tuple[int, int, int]]) -> bytes:
    try:
        result = remove(data, model_name=model_name)
    except TypeError:
        result = remove(data, model=model_name)
    image = Image.open(io.BytesIO(result)).convert("RGBA")
    if bg_color is not None:
        background = Image.new("RGBA", image.size, (*bg_color, 255))
        image = Image.alpha_composite(background, image)
    output_buffer = io.BytesIO()
    image.save(output_buffer, "PNG")
    return output_buffer.getvalue()


def process_file(source_path: Path, output_path: Path, model_name: str, bg_color: Optional[Tuple[int, int, int]], overwrite: bool) -> str:
    if output_path.exists() and not overwrite:
        return f"skipped {source_path.name} (already exists)"
    with source_path.open("rb") as file:
        data = file.read()
    try:
        result = remove(data, model_name=model_name)
    except TypeError:
        result = remove(data, model=model_name)
    image = Image.open(io.BytesIO(result)).convert("RGBA")
    save_png(image, output_path, bg_color)
    return f"processed {source_path.name} -> {output_path.name}"


def run_batch(input_path: Path, output_path: Path, model_name: str, bg_color: Optional[Tuple[int, int, int]], workers: int, overwrite: bool) -> None:
    files = get_input_files(input_path)
    if not files:
        raise FileNotFoundError(f"No supported input images found in {input_path}")

    if input_path.is_file():
        ensure_output_folder(output_path.parent)
    else:
        ensure_output_folder(output_path)

    tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for source_file in files:
            if input_path.is_dir():
                target = output_path / f"{source_file.stem}.png"
            else:
                target = output_path
            tasks.append(executor.submit(process_file, source_file, target, model_name, bg_color, overwrite))

        for done in concurrent.futures.as_completed(tasks):
            print(done.result())


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch remove image backgrounds using rembg.")
    parser.add_argument("--input", help="Input file or folder. Defaults to ./input", default="input")
    parser.add_argument("--output", help="Output folder or file. Defaults to ./output", default="output")
    parser.add_argument("--bg-color", help="Replace transparency with solid RGB background, e.g. 255,255,255", type=parse_color)
    parser.add_argument("--model", help="U²-Net model name", default="u2net")
    parser.add_argument("--workers", help="Number of parallel workers", type=int, default=4)
    parser.add_argument("--overwrite", help="Overwrite existing output files", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_file() and output_path.exists() and output_path.is_dir():
        output_path = output_path / f"{input_path.stem}.png"

    if input_path.is_file() and output_path.suffix.lower() not in {".png"}:
        output_path = output_path.with_suffix(".png")

    if input_path.is_dir() and output_path.suffix.lower() == ".png":
        parser.error("When using a folder input, output must be a folder, not a file.")

    run_batch(input_path, output_path, args.model, args.bg_color, args.workers, args.overwrite)


if __name__ == "__main__":
    main()
