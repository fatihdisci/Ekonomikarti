"""CLI entry point for the morning card."""

from __future__ import annotations

import argparse

from src.pipeline import run_morning


def main() -> None:
    parser = argparse.ArgumentParser(description="Fiyat Hafızası — sabah kartı üret.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use fixtures, no API calls, no OpenRouter",
    )
    args = parser.parse_args()
    path = run_morning(dry_run=args.dry_run)
    print(f"OK: {path}")


if __name__ == "__main__":
    main()
