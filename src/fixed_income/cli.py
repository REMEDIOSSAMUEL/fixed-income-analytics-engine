"""Help-only command line entry point for the scaffold."""

import argparse


def main() -> None:
    """Display scaffold help; financial commands are not yet implemented."""
    parser = argparse.ArgumentParser(
        description=(
            "Educational fixed-income analytics scaffold. "
            "Bond analytics, NSS modelling, and curve risk are planned; "
            "financial functionality is not yet implemented."
        )
    )
    parser.parse_args()
    parser.print_help()


if __name__ == "__main__":
    main()
