"""FastAPI app: REST endpoint + serves the controller UI.

Endpoints (to implement):
    GET  /                -> serves ui/index.html
    POST /review          -> accepts a session JSON, returns a prediction
    POST /decision        -> records controller's final PASS/REJECT/SEND-BACK

Run:
    uvicorn api:app --reload
"""

from fastapi import FastAPI

app = FastAPI(title="Firefighter Log Reviewer")


@app.get("/health")
def health():
    return {"status": "ok"}

# TODO: /review, /decision, and static UI serving.
