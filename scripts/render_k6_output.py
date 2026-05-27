"""Render k6 terminal output as PNG screenshots."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCREEN = ROOT / "screenshots"

BG = (24, 24, 27)
FG = (220, 220, 220)
GREEN = (74, 222, 128)
RED = (248, 113, 113)
YELLOW = (251, 191, 36)
CYAN = (103, 232, 249)
PAD = 24
LINE_H = 18

for path in [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
]:
    if Path(path).exists():
        font = ImageFont.truetype(path, 13)
        break
else:
    font = ImageFont.load_default()


def colour_for(line: str):
    s = line.strip()
    if s.startswith("✓"):
        return GREEN
    if s.startswith("✗") or "FAIL" in s.upper():
        return RED
    if s.startswith("█"):
        return CYAN
    if "p(95)" in s or "p(99)" in s or "thresholds" in s.lower():
        return YELLOW
    return FG


def render(in_path: Path, out_path: Path) -> None:
    lines = in_path.read_text().splitlines()
    width = 1200
    height = PAD * 2 + LINE_H * len(lines)
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((PAD, PAD + i * LINE_H), line, font=font, fill=colour_for(line))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"wrote {out_path}")


render(ROOT / "reports/q4_load_output.txt", SCREEN / "q4_load_run.png")
render(ROOT / "reports/q4_stress_output.txt", SCREEN / "q4_stress_run.png")
