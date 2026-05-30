"""Batch prediction: run the reviewer over a folder of sessions.

Usage:
    python predict.py --sessions dataset_candidate/train/sessions \
                      --out predictions_train.jsonl

Writes one JSON object per line (same shape as labels.jsonl) so it can be
fed straight into eval/eval.py.
"""

import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", required=True, help="folder of session JSON files")
    ap.add_argument("--out", required=True, help="output predictions JSONL")
    args = ap.parse_args()

    session_files = sorted(Path(args.sessions).glob("*.json"))

    with open(args.out, "w", encoding="utf-8") as out:
        for f in session_files:
            raw = json.loads(f.read_text(encoding="utf-8"))
            # TODO: session = Session.model_validate(raw)
            #       prediction = review(session)
            #       out.write(json.dumps(prediction.model_dump(), ensure_ascii=False) + "\n")
            pass

    print(f"Wrote predictions for {len(session_files)} sessions -> {args.out}")


if __name__ == "__main__":
    main()
