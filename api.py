"""FastAPI app: REST endpoint + serves the controller UI."""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse

from ffreviewer.models import Session
from ffreviewer.reviewer import review

app = FastAPI(title="Firefighter Log Reviewer")


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serve the controller UI."""
    html = Path("ui/index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/review")
def review_session(file: UploadFile = File(...)):
    """Accept a session JSON file, return the prediction."""
    try:
        raw = json.loads(file.file.read())
        session = Session.model_validate(raw)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid session file: {e}")
    
    prediction = review(session)
    return JSONResponse(content=json.loads(prediction.model_dump_json()))


# In-memory store for controller decisions (no auth needed per spec)
decisions: dict = {}

@app.post("/decision")
def record_decision(body: dict):
    """Save the controller's final PASS / REJECT / SEND-BACK decision."""
    session_id = body.get("session_id")
    decision   = body.get("decision")
    if not session_id or not decision:
        raise HTTPException(status_code=422, detail="session_id and decision required")
    decisions[session_id] = {"session_id": session_id, "decision": decision}
    # also persist to file so it survives restarts
    Path("decisions.json").write_text(
        json.dumps(list(decisions.values()), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return {"saved": True, "session_id": session_id, "decision": decision}