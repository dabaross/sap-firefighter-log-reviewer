# SAP Firefighter Log Compliance Reviewer

AI-assisted pre-screening of SAP GRC firefighter (emergency access) sessions.
Given one session log, the system returns a verdict
(`PASS` / `REJECT` / `NEEDS_CORRECTION`), a list of compliance findings, and —
for borderline sessions — a drafted clarification message for the firefighter.

> Internship technical challenge submission. Built to be understood and
> defended, not just to score.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
```

Place the challenge dataset next to this repo as `dataset_candidate/`
(it is intentionally not committed).

### Review one session
```bash
python cli.py dataset_candidate/train/sessions/FF-TRAIN-0001.json
```

### Run on a whole set and evaluate
```bash
python predict.py --sessions dataset_candidate/train/sessions --out predictions_train.jsonl
python eval/eval.py --predictions predictions_train.jsonl --labels dataset_candidate/train/labels.jsonl
```

### Controller UI
```bash
uvicorn api:app --reload
# open http://127.0.0.1:8000
```

## How it works

`session JSON -> validate (Pydantic) -> rule engine -> findings -> verdict -> (correction)`

- **Deterministic rules** do the detection and the verdict.
- **Verdict logic:** no findings -> PASS; worst finding `medium` -> NEEDS_CORRECTION; any `high`/`critical` -> REJECT.
- **Templates** draft the clarification message (no external API needed).

## TODO — filled during the build
- [ ] Architecture diagram
- [ ] Full rule catalog + rationale for added rules
- [ ] Deterministic vs. LLM split and why
- [ ] Known failure modes (>= 3 honest examples)
- [ ] Cost estimate per session
- [ ] What I would build next given another week
- [ ] Hours log
- [ ] (Optional) "Where I disagree with the gold label" appendix
