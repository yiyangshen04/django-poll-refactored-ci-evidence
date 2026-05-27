"""Render pytest output text as a PNG that looks like a terminal."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TXT = ROOT / "reports" / "q5_pytest_output.txt"
OUT = ROOT / "screenshots" / "q5_pytest_run.png"

BG = (24, 24, 27)
FG = (220, 220, 220)
GREEN = (74, 222, 128)
RED = (248, 113, 113)
YELLOW = (251, 191, 36)
PAD = 24
LINE_H = 18

font_candidates = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "/Library/Fonts/Menlo.ttc",
]
font = None
for path in font_candidates:
    if Path(path).exists():
        font = ImageFont.truetype(path, 13)
        break
if font is None:
    font = ImageFont.load_default()


def colour_for(line: str):
    if " PASSED" in line:
        return GREEN
    if " FAILED" in line or "ERROR" in line:
        return RED
    if "warning" in line.lower() and "===" in line:
        return YELLOW
    if line.startswith("==="):
        return YELLOW
    return FG


def main() -> None:
    lines = TXT.read_text().splitlines()
    width = 1100
    height = PAD * 2 + LINE_H * len(lines)
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((PAD, PAD + i * LINE_H), line, font=font, fill=colour_for(line))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
