"""Batch: run reviewer over a folder and write predictions.jsonl."""

import argparse
import json
from pathlib import Path

from ffreviewer.models import Session
from ffreviewer.reviewer import review


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    files = sorted(Path(args.sessions).glob("*.json"))
    with open(args.out, "w", encoding="utf-8") as out:
        for f in files:
            raw = json.loads(f.read_text(encoding="utf-8"))
            session = Session.model_validate(raw)
            prediction = review(session)
            out.write(prediction.model_dump_json() + "\n")

    print(f"Done: {len(files)} sessions -> {args.out}")


if __name__ == "__main__":
    main()