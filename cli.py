"""Command-line entry point: review a single session file.

Usage:
    python cli.py path/to/session.json

Prints the prediction as JSON to stdout.
"""

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("Usage: python cli.py <session.json>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    raw = json.loads(path.read_text(encoding="utf-8"))

    # TODO: once models + reviewer are implemented:
    # session = Session.model_validate(raw)
    # prediction = review(session)
    # print(json.dumps(prediction.model_dump(), indent=2, ensure_ascii=False))

    print("CLI wired; reviewer not implemented yet.", file=sys.stderr)


if __name__ == "__main__":
    main()
