# Bulk Background Remover

A Python automation that removes the background from hundreds of images at once using AI (the `rembg` library, powered by the U²-Net model).

## What is included

- `app.py` — Flask web app for drag-and-drop batch background removal.
- `remove_bg.py` — Command line batch processor for folders or single image files.
- `requirements.txt` — Python dependencies.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Web app

```powershell
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Command line usage

```powershell
python remove_bg.py
```

### Examples

```powershell
python remove_bg.py --input "C:\path\to\photos" --output "C:\path\to\results"
python remove_bg.py --input "C:\path\to\photo.jpg"
python remove_bg.py --bg-color 255,255,255
python remove_bg.py --workers 8
python remove_bg.py --overwrite
```

## Notes

- Supported input formats: `jpg`, `jpeg`, `png`, `bmp`, `webp`, `tiff`, `gif`.
- Transparent results are always saved as `PNG`.
- For people photos, try `--model u2net_human_seg` for sharper edges.
