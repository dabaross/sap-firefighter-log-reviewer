"""CLI: review a single session file and print the prediction as JSON."""

import json
import sys
from pathlib import Path

from ffreviewer.models import Session
from ffreviewer.reviewer import review


def main():
    if len(sys.argv) != 2:
        print("Usage: python cli.py <session.json>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    raw = json.loads(path.read_text(encoding="utf-8"))
    session = Session.model_validate(raw)
    prediction = review(session)
    print(prediction.model_dump_json(indent=2))


if __name__ == "__main__":
    main()