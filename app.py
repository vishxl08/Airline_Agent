"""
Customer-Facing Resolution Agent — Airline Disruption
FastAPI backend. Run with: uvicorn app:app --reload --port 8000
Requires env var GROQ_API_KEY (free key from console.groq.com).
"""

import os
import json
import sqlite3
import time
import uuid

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import policy_engine as pe
from data_pack import RULES_TEXT, SAMPLE_TONE

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Llama 3.3 70B is enterprise-gated on many Groq keys. Prefer a model that
# works on the free/developer plan, then fall back.
DEFAULT_GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
]

DB_PATH = os.path.join(os.path.dirname(__file__), "conversations.db")
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def load_env_file():
    """Load KEY=VALUE pairs from .env without overriding already-set env vars."""
    if not os.path.isfile(ENV_PATH):
        return
    with open(ENV_PATH, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_env_file()


def groq_api_key() -> str:
    return os.environ.get("GROQ_API_KEY", "").strip()


def groq_models() -> list:
    override = os.environ.get("GROQ_MODEL", "").strip()
    models = [override] if override else []
    for m in DEFAULT_GROQ_MODELS:
        if m not in models:
            models.append(m)
    return models


app = FastAPI(title="Airline Resolution Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            ts REAL,
            role TEXT,
            message TEXT,
            action_taken TEXT,
            escalated INTEGER
        )
    """)
    con.commit()
    con.close()


init_db()


def log_record(session_id, role, message, action_taken=None, escalated=False):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO records (session_id, ts, role, message, action_taken, escalated) VALUES (?,?,?,?,?,?)",
        (session_id, time.time(), role, message, action_taken, int(escalated)),
    )
    con.commit()
    con.close()


SESSIONS = {}


def call_groq(system_prompt: str, history: list, user_message: str) -> str:
    key = groq_api_key()
    if not key:
        return (
            "[No GROQ_API_KEY set — this is a placeholder reply. "
            "Set the GROQ_API_KEY environment variable (or a local .env file) to enable live responses.]"
        )

    messages = [{"role": "system", "content": system_prompt}]
    for turn in history[-8:]:
        messages.append(turn)
    messages.append({"role": "user", "content": user_message})

    last_error = None
    for model in groq_models():
        try:
            resp = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.4,
                    "max_tokens": 500,
                },
                timeout=45,
            )
        except requests.RequestException as exc:
            last_error = str(exc)
            continue

        if resp.status_code == 200:
            msg = resp.json()["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if content:
                return content
            last_error = f"{model} returned empty content"
            continue

        try:
            err = resp.json().get("error", {}).get("message", resp.text[:200])
        except ValueError:
            err = resp.text[:200]
        last_error = f"{model}: HTTP {resp.status_code} {err}"
        if resp.status_code in (401, 403):
            break

    return (
        "I'm having trouble reaching the language model right now, but I still have your "
        "booking facts. Please try again in a moment. "
        f"(debug: {last_error})"
    )


def build_system_prompt(pnr, customer, all_legs, leg, entitlement, escalations):
    facts = {
        "customer": customer,
        "pnr": pnr,
        "all_booking_legs": all_legs,
        "disrupted_leg": leg,
        "computed_entitlement": entitlement,
        "escalation_required": bool(escalations),
        "escalation_reasons": [r[1] for r in escalations],
    }

    return f"""You are a customer support agent for an airline, handling flight disruptions.

{RULES_TEXT}

{SAMPLE_TONE}

TONE: Be warm, direct, and empathetic — especially if the customer is upset. Never argue.
Acknowledge frustration briefly, then give the correct answer.

HARD RULES YOU MUST FOLLOW:
- CURRENT CASE FACTS below are the live booking. Never say you cannot find the PNR, flight, delay hours, or status if they appear there.
- You may ONLY offer what appears in "computed_entitlement". Never invent extras (no free upgrades, no goodwill cash, no full-night hotel when only delayed-hours hotel applies).
- If the customer asks for something covered by computed_entitlement, confirm you have applied / initiated it.
- If "escalation_required" is true, do NOT approve the out-of-policy parts in escalation_reasons.
  Still apply anything that IS covered. For the rest, escalate to a human specialist and say they will follow up.
  Gold/Platinum tier = priority rebooking only, not extra compensation.
- Keep replies short (3-5 sentences). Ask at most one clarifying question if genuinely needed.

CURRENT CASE FACTS (ground truth — do not contradict these):
{json.dumps(facts, indent=2)}
"""


def determine_action_taken(entitlement, escalations):
    parts = []
    if entitlement:
        if entitlement["type"] == "cancellation":
            parts.append("OFFERED_REBOOK_OR_REFUND")
        elif entitlement["type"] == "delay":
            parts.append("APPLIED_DELAY_COMPENSATION:" + ",".join(entitlement["entitled"]))
        else:
            parts.append("INFO_ONLY")
    if escalations:
        parts.append("ESCALATED: " + "; ".join(code for code, _ in escalations))
    return " | ".join(parts) if parts else "INFO_ONLY"


class ChatIn(BaseModel):
    session_id: str | None = None
    message: str = ""


@app.get("/health")
def health():
    return {
        "ok": True,
        "groq_key_present": bool(groq_api_key()),
        "models": groq_models(),
    }


@app.post("/chat")
def chat(payload: ChatIn):
    session_id = payload.session_id or str(uuid.uuid4())
    session = SESSIONS.setdefault(session_id, {"pnr": None, "history": []})

    user_message = (payload.message or "").strip()
    if not user_message:
        return {
            "session_id": session_id,
            "reply": "Please type a message so I can help.",
            "action_taken": "INFO_ONLY",
            "escalated": False,
        }

    log_record(session_id, "user", user_message)

    found = pe.find_pnr_in_text(user_message)
    if found and found != session.get("pnr"):
        session["pnr"] = found
        session["history"] = []

    pnr = pe.resolve_pnr(session.get("pnr"), user_message)
    session["pnr"] = pnr

    if not pnr:
        reply = (
            "Hi! I'd be happy to help. Could you share your booking reference "
            "(PNR) so I can pull up your flight details?"
        )
        session["history"].append({"role": "user", "content": user_message})
        session["history"].append({"role": "assistant", "content": reply})
        log_record(session_id, "agent", reply, action_taken="ASKED_FOR_PNR")
        return {
            "session_id": session_id,
            "reply": reply,
            "action_taken": "ASKED_FOR_PNR",
            "escalated": False,
        }

    customer = pe.get_customer(pnr)
    all_legs = pe.get_bookings(pnr)
    leg = pe.get_active_leg(pnr)
    entitlement = pe.entitlement_for_leg(leg) if leg else None
    escalations = pe.detect_escalation_triggers(user_message, leg)

    system_prompt = build_system_prompt(pnr, customer, all_legs, leg, entitlement, escalations)
    reply = call_groq(system_prompt, session["history"], user_message)

    action_taken = determine_action_taken(entitlement, escalations)
    escalated = bool(escalations)

    session["history"].append({"role": "user", "content": user_message})
    session["history"].append({"role": "assistant", "content": reply})
    log_record(session_id, "agent", reply, action_taken=action_taken, escalated=escalated)

    return {
        "session_id": session_id,
        "reply": reply,
        "action_taken": action_taken,
        "escalated": escalated,
        "customer": customer,
        "pnr": pnr,
        "legs": all_legs,
        "entitlement": entitlement,
    }


@app.get("/history/{session_id}")
def get_history(session_id: str):
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT ts, role, message, action_taken, escalated FROM records WHERE session_id=? ORDER BY id",
        (session_id,),
    ).fetchall()
    con.close()
    return [
        {"ts": r[0], "role": r[1], "message": r[2], "action_taken": r[3], "escalated": bool(r[4])}
        for r in rows
    ]


@app.post("/reset")
def reset(payload: ChatIn):
    session_id = payload.session_id
    if session_id in SESSIONS:
        del SESSIONS[session_id]
    return {"ok": True}


@app.get("/")
def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))


app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
