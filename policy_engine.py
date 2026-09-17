"""
Deterministic Policy Engine.

Design decision: the LLM is NEVER trusted to compute policy outcomes (delay
thresholds, fare-difference limits, escalation triggers). All of that is
computed here, in plain Python, from the data pack. The LLM only handles
conversation tone and communicating the already-computed facts.
"""

import re
from data_pack import CUSTOMERS, BOOKINGS

PNR_PATTERN = re.compile(r"\b(SK4821X|TR1190B|WL7742)\b", re.IGNORECASE)

ESCALATION_KEYWORDS = {
    "legal_threat": ["legal action", "sue", "lawsuit", "lawyer", "court", "consumer forum"],
    "formal_complaint": ["formal complaint", "file a complaint", "filing a complaint"],
    "upgrade_request": ["upgrade", "business class", "first class"],
    "extra_compensation": [
        "extra compensation", "compensate me", "for the trouble",
        "extra money", "compensation for", "additional compensation",
        "cash bonus", "goodwill",
    ],
    "full_night_stay": [
        "full night", "entire night", "whole night stay", "full night's stay",
        "overnight", "night stay", "night's stay",
    ],
    "different_payment_method": [
        "different card", "different account", "another payment method",
        "different bank", "another card", "other card", "other account",
    ],
}

HOTEL_KEYWORDS = ["hotel", "accommodation"]


def find_pnr_in_text(text: str):
    match = PNR_PATTERN.search(text)
    return match.group(1).upper() if match else None


def resolve_pnr(current_pnr: str | None, text: str):
    """Use a PNR mentioned in this message; otherwise keep the session PNR."""
    found = find_pnr_in_text(text)
    return found or current_pnr


def get_customer(pnr: str):
    return CUSTOMERS.get(pnr.upper()) if pnr else None


def get_bookings(pnr: str):
    return BOOKINGS.get(pnr.upper(), []) if pnr else []


def get_active_leg(pnr: str):
    """Return the leg that's actually disrupted (cancelled/delayed), if any."""
    for leg in get_bookings(pnr):
        if leg["status"] in ("cancelled", "delayed"):
            return leg
    return None


def entitlement_for_leg(leg: dict):
    """Compute exactly what the customer is entitled to for a given leg."""
    if not leg:
        return None

    if leg["status"] == "cancelled":
        return {
            "type": "cancellation",
            "entitled": [
                "Free rebooking on the next available flight within 24 hours, OR",
                "A full refund to the original payment method (customer's choice)",
            ],
            "includes_hotel": False,
        }

    if leg["status"] == "delayed":
        h = leg["delay_hours"]
        # Rules: under 3h → ₹500 meal; more than 3h → meal + lounge; more than 5h → + hotel (delayed hours only)
        if h < 3:
            items = ["₹500 meal voucher"]
            includes_hotel = False
        elif h <= 5:
            items = ["meal voucher", "lounge access"]
            includes_hotel = False
        else:
            items = [
                "meal voucher",
                "lounge access",
                "hotel accommodation (ONLY for the delayed hours, not a full night)",
            ]
            includes_hotel = True
        return {
            "type": "delay",
            "delay_hours": h,
            "entitled": items,
            "includes_hotel": includes_hotel,
        }

    return {"type": "unaffected", "entitled": [], "includes_hotel": False}


def detect_escalation_triggers(message: str, leg: dict, fare_diff_amount: int = None):
    """
    Scan the customer's message (+ known booking facts) for anything that
    must be escalated per the Prohibited Actions list. Returns a list of
    (reason_code, human_reason) tuples. Empty list = no escalation needed.
    """
    msg = message.lower()
    reasons = []
    seen = set()

    def add(code, label):
        if code not in seen:
            seen.add(code)
            reasons.append((code, label))

    labels = {
        "legal_threat": "Customer raised threat of legal action — must escalate immediately.",
        "formal_complaint": "Customer wants to file a formal complaint — must escalate immediately.",
        "upgrade_request": "Free upgrade is not part of policy entitlement — requires escalation.",
        "extra_compensation": "Compensation beyond standard policy requested — requires escalation.",
        "full_night_stay": "Full night hotel stay exceeds policy (delayed-hours-only) — requires escalation.",
        "different_payment_method": "Refund to a different payment method is prohibited — requires escalation.",
    }

    for code, kws in ESCALATION_KEYWORDS.items():
        if any(kw in msg for kw in kws):
            add(code, labels[code])

    # Asking for hotel when delay is under the >5h threshold is out of policy
    entitlement = entitlement_for_leg(leg) if leg else None
    wants_hotel = any(kw in msg for kw in HOTEL_KEYWORDS)
    if wants_hotel and entitlement and not entitlement.get("includes_hotel"):
        add(
            "hotel_not_entitled",
            "Hotel accommodation is not part of this booking's delay entitlement — requires escalation.",
        )

    amt = fare_diff_amount
    if amt is None:
        m = re.search(r"(?:\brs\.?|\binr|₹)\s*(\d[\d,]*)", message, re.IGNORECASE)
        if not m:
            m = re.search(
                r"\b(?:fare difference|fare diff|difference|extra)\b\s*(?:is|of|amount|costs?)?\s*(?:₹|\brs\.?|\binr)?\s*(\d[\d,]*)",
                message,
                re.IGNORECASE,
            )
        if not m:
            m = re.search(r"(\d[\d,]*)\s*(?:\b(?:rupees|inr)\b|\brs\.?|fare difference)", message, re.IGNORECASE)
        if m and m.group(1).replace(",", "").isdigit():
            amt = int(m.group(1).replace(",", ""))

    if amt is not None and amt > 1500:
        add(
            "fare_difference_exceeds_threshold",
            f"Fare difference of ₹{amt} exceeds the ₹1,500 limit agents can waive — requires supervisor approval.",
        )

    if leg and leg.get("status") == "unaffected" and any(
        w in msg for w in ["refund", "compensation", "voucher", "rebook"]
    ):
        add(
            "non_airline_caused",
            "This leg is unaffected / not airline-caused — exceptions here must be escalated.",
        )

    return reasons
