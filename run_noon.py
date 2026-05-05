"""CLI entry point for the noon "Odak Kartı"."""

from __future__ import annotations

import argparse

from src.pipeline import run_noon


def main() -> None:
    parser = argparse.ArgumentParser(description="Fiyat Hafızası — öğle Odak Kartı üret.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use fixtures, no API calls, no OpenRouter",
    )
    parser.add_argument(
        "--focus",
        choices=["usd_try", "eur_try", "gram_altin", "brent", "bist_100"],
        default=None,
        help="Override the rotation and force a specific focus indicator",
    )
    args = parser.parse_args()
    path = run_noon(dry_run=args.dry_run, focus_key=args.focus)
    print(f"OK: {path}")


if __name__ == "__main__":
    main()
