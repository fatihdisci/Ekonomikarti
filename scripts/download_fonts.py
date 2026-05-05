"""Download Inter and JetBrains Mono TTF files for the renderer.

Inter is fetched from the official rsms/inter GitHub release zip and the
required static weights are extracted. JetBrains Mono is fetched directly
from the JetBrains/JetBrainsMono repo.

Run once after cloning, and as a CI step before rendering. Files land in
assets/fonts/ and are gitignored.
"""

from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "assets" / "fonts"

INTER_RELEASE_URL = "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"
INTER_FILES = {
    "extras/ttf/Inter-Regular.ttf": "Inter-Regular.ttf",
    "extras/ttf/Inter-SemiBold.ttf": "Inter-SemiBold.ttf",
    "extras/ttf/Inter-Bold.ttf": "Inter-Bold.ttf",
}

JETBRAINS_FILES: list[tuple[str, str]] = [
    (
        "JetBrainsMono-Medium.ttf",
        "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Medium.ttf",
    ),
    (
        "JetBrainsMono-Bold.ttf",
        "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Bold.ttf",
    ),
]


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "fiyat-hafizasi-font-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _all_present() -> bool:
    targets = list(INTER_FILES.values()) + [name for name, _ in JETBRAINS_FILES]
    return all((FONT_DIR / name).exists() and (FONT_DIR / name).stat().st_size > 1024 for name in targets)


def _extract_inter() -> None:
    needed = [
        FONT_DIR / out for _, out in INTER_FILES.items()
        if not (FONT_DIR / out).exists() or (FONT_DIR / out).stat().st_size < 1024
    ]
    if not needed:
        print("  skip Inter zip (all weights already present)")
        return
    print(f"  fetch Inter release <- {INTER_RELEASE_URL}")
    blob = _http_get(INTER_RELEASE_URL)
    print(f"  ok   Inter release ({len(blob)} bytes)")
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for member, out_name in INTER_FILES.items():
            dest = FONT_DIR / out_name
            if dest.exists() and dest.stat().st_size > 1024:
                continue
            with zf.open(member) as src:
                dest.write_bytes(src.read())
            print(f"  extract {out_name} ({dest.stat().st_size} bytes)")


def _fetch_jetbrains() -> None:
    for filename, url in JETBRAINS_FILES:
        dest = FONT_DIR / filename
        if dest.exists() and dest.stat().st_size > 1024:
            print(f"  skip {filename} (already present)")
            continue
        print(f"  fetch {filename} <- {url}")
        data = _http_get(url)
        if len(data) < 1024:
            raise RuntimeError(f"suspiciously small file from {url}: {len(data)} bytes")
        dest.write_bytes(data)
        print(f"  ok   {filename} ({dest.stat().st_size} bytes)")


def main() -> int:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        _extract_inter()
        _fetch_jetbrains()
    except Exception as exc:  # noqa: BLE001
        print(f"\nFAILED: {exc}", file=sys.stderr)
        return 1
    if not _all_present():
        print("\nFAILED: some font files still missing after run", file=sys.stderr)
        return 1
    print("\nAll fonts present in assets/fonts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
