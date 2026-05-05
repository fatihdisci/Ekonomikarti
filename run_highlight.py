"""CLI entry point for the Sunday star/loser highlight card."""

from __future__ import annotations

import argparse

from src.pipeline import run_highlight


def main() -> None:
    parser = argparse.ArgumentParser(description="Fiyat Hafızası — Pazar Yıldız/Kaybeden kartı.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use fixtures, no API calls, no OpenRouter",
    )
    args = parser.parse_args()
    path = run_highlight(dry_run=args.dry_run)
    print(f"OK: {path}")


if __name__ == "__main__":
    main()
