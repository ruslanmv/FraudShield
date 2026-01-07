from __future__  import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..core.settings import settings
from ..data.db import init_db
from ..core.workflow import decision_only, investigate_optional
from ..monitoring.kpis import compute_kpis
from ..tools import enrichment as E

class DecisionRequest(BaseModel):
    trans_id: str

class InvestigateRequest(BaseModel):
    trans_id: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Production-friendly: always init DB on boot (demo)
    init_db()
    yield

app = FastAPI(title="FraudShield API", version="0.5.0", lifespan=lifespan)

s = settings()
allow_origins = [o.strip() for o in (s.cors_allow_origins or "").split(",") if o.strip()]
if allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def verify_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if s.api_key and x_api_key != s.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return True

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.5.0"}

@app.post("/decision", dependencies=[Depends(verify_key)])
def decision(req: DecisionRequest):
    out = decision_only(req.trans_id)
    if out.get("error"):
        raise HTTPException(status_code=404, detail=out["error"])
    return out


@app.get("/case/{trans_id}", dependencies=[Depends(verify_key)])
def case(trans_id: str):
    """Fetch case context for the ops UI (PII redacted by default)."""
    txn = E.lookup_transaction(trans_id)
    if not txn.get("found"):
        raise HTTPException(status_code=404, detail="transaction_not_found")

    t = txn["transaction"]
    user_id = t.get("user_id")

    return {
        "transaction_id": trans_id,
        "transaction": t,
        "user_history": E.lookup_user_history(user_id) if user_id else {},
        "ip_intel": E.lookup_ip_intel(t.get("device_ip", "")),
        "kyc": E.lookup_kyc(user_id) if user_id else {},
        "disputes": E.lookup_disputes(user_id) if user_id else {},
        "similar_cases": E.find_similar_cases_stub(trans_id),
    }

@app.post("/investigate", dependencies=[Depends(verify_key)])
def investigate(req: InvestigateRequest):
    out = investigate_optional(req.trans_id)
    if out.get("error") == "transaction_not_found":
        raise HTTPException(status_code=404, detail=out["error"])
    # If ops extra missing, return 409 conflict (capability not installed)
    if out.get("error") == "ops_extra_not_installed":
        raise HTTPException(status_code=409, detail=out.get("message", "ops extra not installed"))
    if out.get("error") == "missing_openai_api_key":
        raise HTTPException(status_code=400, detail=out.get("message", "missing OPENAI_API_KEY"))
    return out

@app.get("/kpis", dependencies=[Depends(verify_key)])
def kpis(window_days: int = 30):
    return compute_kpis(window_days=window_days)
